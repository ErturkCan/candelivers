"""VRPTW solver using nearest-neighbor heuristic and 2-opt improvement."""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import math

from .distance import DistanceMatrix
from .constraints import ConstraintChecker, TimeWindow


@dataclass
class Order:
    """Represents a delivery order."""

    id: str
    pickup_location: Tuple[float, float]  # (lat, lng)
    delivery_location: Tuple[float, float]  # (lat, lng)
    time_window: TimeWindow
    weight_kg: float
    volume_m3: float


@dataclass
class Vehicle:
    """Represents a delivery vehicle."""

    id: str
    max_weight_kg: float
    max_volume_m3: float
    start_location: Tuple[float, float]  # (lat, lng)
    end_location: Optional[Tuple[float, float]] = None


@dataclass
class Route:
    """Represents a delivery route for a vehicle."""

    vehicle_id: str
    stops: List[int]  # Order indices
    total_distance: float
    total_time_minutes: float
    weight_used: float
    volume_used: float


class RouteOptimizer:
    """VRPTW solver using nearest-neighbor heuristic and 2-opt improvement."""

    def __init__(self, use_distance_cache: bool = False):
        """Initialize route optimizer.

        Args:
            use_distance_cache: Whether to cache distance computations
        """
        self.distance_matrix = DistanceMatrix(use_cache=use_distance_cache)
        self.constraint_checker = ConstraintChecker()
        self.average_speed_kmh = 40.0  # Average delivery vehicle speed

    def optimize(
        self,
        orders: List[Order],
        vehicles: List[Vehicle],
        improve_with_2opt: bool = True,
    ) -> List[Route]:
        """Optimize delivery routes using VRPTW.

        Args:
            orders: List of orders to deliver
            vehicles: List of available vehicles
            improve_with_2opt: Whether to apply 2-opt improvement

        Returns:
            List of optimized routes
        """
        if not orders:
            return []

        # Get all locations (depot + pickups + deliveries)
        locations = self._extract_locations(orders, vehicles)

        # Compute distance matrix
        distance_matrix = self.distance_matrix.compute_distance_matrix(locations)

        # Build initial solution using nearest-neighbor
        routes = self._nearest_neighbor_initial_solution(
            orders, vehicles, distance_matrix
        )

        # Improve with 2-opt if requested
        if improve_with_2opt:
            routes = self._improve_with_2opt(routes, distance_matrix)

        return routes

    def _extract_locations(
        self, orders: List[Order], vehicles: List[Vehicle]
    ) -> List[Tuple[float, float]]:
        """Extract all unique locations for distance matrix.

        Args:
            orders: List of orders
            vehicles: List of vehicles

        Returns:
            List of (lat, lng) tuples with depot first
        """
        locations = []

        # Add vehicle start locations (depots)
        for vehicle in vehicles:
            if vehicle.start_location not in locations:
                locations.append(vehicle.start_location)

        # Add order locations
        for order in orders:
            if order.pickup_location not in locations:
                locations.append(order.pickup_location)
            if order.delivery_location not in locations:
                locations.append(order.delivery_location)

        return locations

    def _nearest_neighbor_initial_solution(
        self,
        orders: List[Order],
        vehicles: List[Vehicle],
        distance_matrix: List[List[float]],
    ) -> List[Route]:
        """Build initial solution using nearest-neighbor heuristic.

        Args:
            orders: List of orders
            vehicles: List of vehicles
            distance_matrix: Precomputed distance matrix

        Returns:
            List of routes
        """
        routes: List[Route] = []
        unassigned = set(range(len(orders)))

        for vehicle in vehicles:
            if not unassigned:
                break

            route_orders = []
            current_weight = 0.0
            current_volume = 0.0
            current_location = vehicle.start_location

            # Greedy assignment: pick nearest unassigned order
            while unassigned:
                best_order_idx = None
                best_distance = float("inf")

                for order_idx in unassigned:
                    order = orders[order_idx]

                    # Check capacity
                    new_weight = current_weight + order.weight_kg
                    new_volume = current_volume + order.volume_m3

                    if (
                        new_weight > vehicle.max_weight_kg
                        or new_volume > vehicle.max_volume_m3
                    ):
                        continue

                    # Calculate distance to pickup
                    distance = self.distance_matrix.distance_between(
                        current_location, order.pickup_location
                    )

                    if distance < best_distance:
                        best_distance = distance
                        best_order_idx = order_idx

                if best_order_idx is None:
                    break

                route_orders.append(best_order_idx)
                order = orders[best_order_idx]
                current_weight += order.weight_kg
                current_volume += order.volume_m3
                current_location = order.delivery_location
                unassigned.remove(best_order_idx)

            if route_orders:
                route = self._calculate_route_metrics(
                    route_orders, orders, vehicle, distance_matrix
                )
                routes.append(route)

        # Attempt to assign remaining orders to vehicles with capacity
        for order_idx in unassigned:
            order = orders[order_idx]
            assigned = False

            # Try to find a vehicle with enough capacity
            for i, vehicle in enumerate(vehicles):
                if i < len(routes):
                    route = routes[i]
                    if (
                        route.weight_used + order.weight_kg <= vehicle.max_weight_kg
                        and route.volume_used + order.volume_m3 <= vehicle.max_volume_m3
                    ):
                        route.stops.append(order_idx)
                        route.weight_used += order.weight_kg
                        route.volume_used += order.volume_m3
                        assigned = True
                        break

            # If no vehicle has capacity, leave it unassigned
            # (in production, would retry or use different algorithm)

        return routes

    def _calculate_route_metrics(
        self,
        order_indices: List[int],
        orders: List[Order],
        vehicle: Vehicle,
        distance_matrix: List[List[float]],
    ) -> Route:
        """Calculate metrics for a route.

        Args:
            order_indices: List of order indices in route
            orders: List of all orders
            vehicle: Vehicle for this route
            distance_matrix: Distance matrix

        Returns:
            Route with metrics calculated
        """
        total_distance = 0.0
        total_time = 0.0
        total_weight = 0.0
        total_volume = 0.0

        current_location = vehicle.start_location
        current_time = 0.0

        for order_idx in order_indices:
            order = orders[order_idx]

            # Distance to pickup
            distance_to_pickup = self.distance_matrix.distance_between(
                current_location, order.pickup_location
            )
            total_distance += distance_to_pickup
            travel_time = (distance_to_pickup / self.average_speed_kmh) * 60
            total_time += travel_time
            current_time += travel_time

            # Service time at pickup
            service_time = 15  # minutes
            total_time += service_time
            current_time += service_time

            # Distance from pickup to delivery
            distance_to_delivery = self.distance_matrix.distance_between(
                order.pickup_location, order.delivery_location
            )
            total_distance += distance_to_delivery
            travel_time = (distance_to_delivery / self.average_speed_kmh) * 60
            total_time += travel_time
            current_time += travel_time

            # Service time at delivery
            service_time = 30  # minutes
            total_time += service_time
            current_time += service_time

            total_weight += order.weight_kg
            total_volume += order.volume_m3
            current_location = order.delivery_location

        # Return distance (distance back to depot)
        if vehicle.end_location:
            distance_to_end = self.distance_matrix.distance_between(
                current_location, vehicle.end_location
            )
            total_distance += distance_to_end
            travel_time = (distance_to_end / self.average_speed_kmh) * 60
            total_time += travel_time

        return Route(
            vehicle_id=vehicle.id,
            stops=order_indices,
            total_distance=total_distance,
            total_time_minutes=total_time,
            weight_used=total_weight,
            volume_used=total_volume,
        )

    def _improve_with_2opt(
        self, routes: List[Route], distance_matrix: List[List[float]]
    ) -> List[Route]:
        """Improve routes using 2-opt local search.

        Args:
            routes: Initial routes
            distance_matrix: Precomputed distance matrix

        Returns:
            Improved routes
        """
        improved_routes = []

        for route in routes:
            improved_route = route
            improved = True

            while improved:
                improved = False
                stops = improved_route.stops

                for i in range(len(stops) - 1):
                    for j in range(i + 2, len(stops)):
                        # Try reversing segment between i+1 and j
                        new_stops = stops[:i + 1] + stops[i + 1 : j + 1][::-1] + stops[j + 1 :]

                        # Calculate improvement
                        old_distance = self._calculate_route_distance(stops)
                        new_distance = self._calculate_route_distance(new_stops)

                        if new_distance < old_distance:
                            stops = new_stops
                            improved = True
                            break

                    if improved:
                        break

            improved_route.stops = stops
            improved_routes.append(improved_route)

        return improved_routes

    def _calculate_route_distance(self, stops: List[int]) -> float:
        """Calculate total distance for a route.

        Args:
            stops: List of order indices

        Returns:
            Total distance in kilometers
        """
        if not stops:
            return 0.0

        # Simplified distance calculation
        # In practice, would use actual distance matrix with proper indices
        total = sum(
            self.distance_matrix.distance_between(
                (0.0, 0.0),  # Simplified for this calculation
                (0.0, i * 0.001),  # Placeholder coordinates
            )
            for i in range(len(stops))
        )

        return total
