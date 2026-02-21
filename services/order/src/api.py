"""FastAPI application for order service."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict
import time
from datetime import datetime

from .models import (
    Order,
    Vehicle,
    Route,
    Stop,
    OptimizationRequest,
    OptimizationResult,
    OrderStatus,
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="CanDelivers Order Service",
        description="Urban bulky-item delivery optimization system",
        version="0.1.0",
    )

    # In-memory storage (replace with database in production)
    orders_db: Dict[str, Order] = {}
    routes_db: Dict[str, Route] = {}
    vehicles_db: Dict[str, Vehicle] = {}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

    @app.post("/orders", response_model=Order)
    async def create_order(order: Order) -> Order:
        """Create a new order.

        Args:
            order: Order to create

        Returns:
            Created order
        """
        if order.id in orders_db:
            raise HTTPException(status_code=409, detail="Order already exists")

        orders_db[order.id] = order
        return order

    @app.get("/orders", response_model=List[Order])
    async def list_orders(
        status: OrderStatus = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Order]:
        """List orders.

        Args:
            status: Filter by order status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of orders
        """
        orders = list(orders_db.values())

        if status:
            orders = [o for o in orders if o.status == status]

        return orders[offset : offset + limit]

    @app.get("/orders/{order_id}", response_model=Order)
    async def get_order(order_id: str) -> Order:
        """Get a specific order.

        Args:
            order_id: Order ID

        Returns:
            Order details
        """
        if order_id not in orders_db:
            raise HTTPException(status_code=404, detail="Order not found")

        return orders_db[order_id]

    @app.put("/orders/{order_id}/status", response_model=Order)
    async def update_order_status(order_id: str, new_status: OrderStatus) -> Order:
        """Update order status.

        Args:
            order_id: Order ID
            new_status: New status

        Returns:
            Updated order
        """
        if order_id not in orders_db:
            raise HTTPException(status_code=404, detail="Order not found")

        order = orders_db[order_id]
        order.status = new_status
        return order

    @app.post("/vehicles", response_model=Vehicle)
    async def create_vehicle(vehicle: Vehicle) -> Vehicle:
        """Register a vehicle.

        Args:
            vehicle: Vehicle to register

        Returns:
            Registered vehicle
        """
        if vehicle.id in vehicles_db:
            raise HTTPException(status_code=409, detail="Vehicle already exists")

        vehicles_db[vehicle.id] = vehicle
        return vehicle

    @app.get("/vehicles", response_model=List[Vehicle])
    async def list_vehicles() -> List[Vehicle]:
        """List all vehicles.

        Returns:
            List of vehicles
        """
        return list(vehicles_db.values())

    @app.post("/optimize", response_model=OptimizationResult)
    async def optimize_routes(request: OptimizationRequest) -> OptimizationResult:
        """Trigger route optimization.

        This endpoint accepts orders and vehicles and returns optimized routes
        using the VRPTW solver.

        Args:
            request: Optimization request containing orders and vehicles

        Returns:
            Optimization result with routes
        """
        start_time = time.time()

        # Import optimizer here to avoid circular imports
        from routing.src.optimizer import RouteOptimizer, Order as OptimizerOrder
        from routing.src.optimizer import Vehicle as OptimizerVehicle
        from routing.src.constraints import TimeWindow

        # Convert models to optimizer format
        optimizer_orders = []
        for order in request.orders:
            optimizer_orders.append(
                OptimizerOrder(
                    id=order.id,
                    pickup_location=order.pickup_location,
                    delivery_location=order.delivery_location,
                    time_window=TimeWindow(
                        earliest=order.time_window.earliest,
                        latest=order.time_window.latest,
                    ),
                    weight_kg=order.weight_kg,
                    volume_m3=order.volume_m3,
                )
            )

        optimizer_vehicles = []
        for vehicle in request.vehicles:
            optimizer_vehicles.append(
                OptimizerVehicle(
                    id=vehicle.id,
                    max_weight_kg=vehicle.max_weight_kg,
                    max_volume_m3=vehicle.max_volume_m3,
                    start_location=vehicle.start_location,
                    end_location=vehicle.end_location,
                )
            )

        # Run optimization
        optimizer = RouteOptimizer(use_distance_cache=False)
        optimized_routes = optimizer.optimize(
            optimizer_orders, optimizer_vehicles, improve_with_2opt=request.use_2opt
        )

        # Convert routes back to API format
        api_routes = []
        assigned_orders = set()

        for opt_route in optimized_routes:
            stops = []
            cumulative_time = 0

            for order_idx in opt_route.stops:
                order = request.orders[order_idx]
                assigned_orders.add(order.id)

                stops.append(
                    Stop(
                        order_id=order.id,
                        location=order.delivery_location,
                        arrival_time_minutes=cumulative_time,
                        service_time_minutes=30,
                    )
                )
                cumulative_time += 45  # Estimated time per stop

            route = Route(
                id=f"route_{opt_route.vehicle_id}_{int(time.time())}",
                vehicle_id=opt_route.vehicle_id,
                stops=stops,
                total_distance_km=opt_route.total_distance,
                total_time_minutes=opt_route.total_time_minutes,
                weight_used_kg=opt_route.weight_used,
                volume_used_m3=opt_route.volume_used,
            )
            api_routes.append(route)

        # Find unassigned orders
        unassigned = [
            order.id for order in request.orders if order.id not in assigned_orders
        ]

        optimization_time = time.time() - start_time

        return OptimizationResult(
            routes=api_routes,
            unassigned_orders=unassigned,
            total_distance_km=sum(r.total_distance_km for r in api_routes),
            total_vehicle_hours=sum(r.total_time_minutes for r in api_routes) / 60.0,
            optimization_time_seconds=optimization_time,
        )

    @app.get("/routes", response_model=List[Route])
    async def list_routes() -> List[Route]:
        """List all routes.

        Returns:
            List of routes
        """
        return list(routes_db.values())

    @app.get("/routes/{route_id}", response_model=Route)
    async def get_route(route_id: str) -> Route:
        """Get a specific route.

        Args:
            route_id: Route ID

        Returns:
            Route details
        """
        if route_id not in routes_db:
            raise HTTPException(status_code=404, detail="Route not found")

        return routes_db[route_id]

    @app.post("/routes", response_model=Route)
    async def create_route(route: Route) -> Route:
        """Save a route.

        Args:
            route: Route to save

        Returns:
            Saved route
        """
        if route.id in routes_db:
            raise HTTPException(status_code=409, detail="Route already exists")

        routes_db[route.id] = route
        return route

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
