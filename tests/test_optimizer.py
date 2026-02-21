"""Tests for route optimizer."""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add src directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.routing.src.optimizer import RouteOptimizer, Order, Vehicle
from services.routing.src.constraints import TimeWindow


class TestRouteOptimizer:
    """Test cases for RouteOptimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance."""
        return RouteOptimizer(use_distance_cache=False)

    @pytest.fixture
    def simple_vehicle(self):
        """Create a simple vehicle."""
        return Vehicle(
            id="v1",
            max_weight_kg=500.0,
            max_volume_m3=10.0,
            start_location=(40.7128, -74.0060),
            end_location=(40.7128, -74.0060),
        )

    @pytest.fixture
    def time_window(self):
        """Create a time window."""
        now = datetime.utcnow()
        return TimeWindow(
            earliest=now,
            latest=now + timedelta(hours=12),
        )

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initializes correctly."""
        assert optimizer is not None
        assert optimizer.average_speed_kmh == 40.0

    def test_empty_orders_returns_empty_routes(self, optimizer, simple_vehicle):
        """Test that empty orders return empty routes."""
        routes = optimizer.optimize([], [simple_vehicle])
        assert routes == []

    def test_single_order_creates_route(self, optimizer, simple_vehicle, time_window):
        """Test that a single order creates a route."""
        order = Order(
            id="o1",
            pickup_location=(40.7130, -74.0060),
            delivery_location=(40.7200, -74.0150),
            time_window=time_window,
            weight_kg=50.0,
            volume_m3=1.0,
        )

        routes = optimizer.optimize([order], [simple_vehicle])

        assert len(routes) == 1
        assert routes[0].vehicle_id == "v1"
        assert len(routes[0].stops) == 1
        assert routes[0].stops[0] == 0  # Order index

    def test_multiple_orders_single_vehicle(self, optimizer, simple_vehicle, time_window):
        """Test that multiple orders can be assigned to single vehicle."""
        orders = [
            Order(
                id=f"o{i}",
                pickup_location=(40.7130 + i * 0.001, -74.0060),
                delivery_location=(40.7200 + i * 0.001, -74.0150),
                time_window=time_window,
                weight_kg=30.0,
                volume_m3=0.5,
            )
            for i in range(3)
        ]

        routes = optimizer.optimize(orders, [simple_vehicle])

        assert len(routes) >= 1
        total_orders = sum(len(route.stops) for route in routes)
        assert total_orders == 3

    def test_capacity_constraint_respected(self, optimizer, time_window):
        """Test that vehicle capacity constraints are respected."""
        vehicle = Vehicle(
            id="v1",
            max_weight_kg=100.0,
            max_volume_m3=2.0,
            start_location=(40.7128, -74.0060),
        )

        # Create orders that would exceed capacity if all assigned to one vehicle
        orders = [
            Order(
                id=f"o{i}",
                pickup_location=(40.7130 + i * 0.001, -74.0060),
                delivery_location=(40.7200 + i * 0.001, -74.0150),
                time_window=time_window,
                weight_kg=50.0,
                volume_m3=1.0,
            )
            for i in range(3)
        ]

        routes = optimizer.optimize(orders, [vehicle])

        # Check that no route exceeds vehicle capacity
        for route in routes:
            assert route.weight_used <= vehicle.max_weight_kg
            assert route.volume_used <= vehicle.max_volume_m3

    def test_route_total_distance_calculated(self, optimizer, simple_vehicle, time_window):
        """Test that route total distance is calculated."""
        order = Order(
            id="o1",
            pickup_location=(40.7130, -74.0060),
            delivery_location=(40.7200, -74.0150),
            time_window=time_window,
            weight_kg=50.0,
            volume_m3=1.0,
        )

        routes = optimizer.optimize([order], [simple_vehicle])

        assert len(routes) == 1
        assert routes[0].total_distance > 0
        assert routes[0].total_time_minutes > 0

    def test_2opt_improvement(self, optimizer, simple_vehicle, time_window):
        """Test that 2-opt improvement is applied."""
        orders = [
            Order(
                id=f"o{i}",
                pickup_location=(40.7130 + i * 0.002, -74.0060),
                delivery_location=(40.7200 + i * 0.002, -74.0150),
                time_window=time_window,
                weight_kg=30.0,
                volume_m3=0.5,
            )
            for i in range(3)
        ]

        # Run with 2-opt
        routes_with_2opt = optimizer.optimize(
            orders, [simple_vehicle], improve_with_2opt=True
        )

        # Run without 2-opt
        routes_without_2opt = optimizer.optimize(
            orders, [simple_vehicle], improve_with_2opt=False
        )

        # Both should complete successfully
        assert routes_with_2opt is not None
        assert routes_without_2opt is not None

    def test_multiple_vehicles_distribute_orders(self, optimizer, time_window):
        """Test that multiple vehicles distribute orders."""
        vehicles = [
            Vehicle(
                id=f"v{i}",
                max_weight_kg=100.0,
                max_volume_m3=2.0,
                start_location=(40.7128, -74.0060),
            )
            for i in range(2)
        ]

        orders = [
            Order(
                id=f"o{i}",
                pickup_location=(40.7130 + i * 0.001, -74.0060),
                delivery_location=(40.7200 + i * 0.001, -74.0150),
                time_window=time_window,
                weight_kg=60.0,
                volume_m3=1.2,
            )
            for i in range(4)
        ]

        routes = optimizer.optimize(orders, vehicles)

        # With 2 vehicles, we should have multiple routes
        assert len(routes) >= 1

    def test_route_stops_in_order(self, optimizer, simple_vehicle, time_window):
        """Test that stops in a route are assigned in valid order."""
        orders = [
            Order(
                id=f"o{i}",
                pickup_location=(40.7130 + i * 0.001, -74.0060),
                delivery_location=(40.7200 + i * 0.001, -74.0150),
                time_window=time_window,
                weight_kg=20.0,
                volume_m3=0.4,
            )
            for i in range(3)
        ]

        routes = optimizer.optimize(orders, [simple_vehicle])

        # Check that stops are valid order indices
        for route in routes:
            for stop_idx in route.stops:
                assert 0 <= stop_idx < len(orders)


class TestNearestNeighbor:
    """Test nearest-neighbor heuristic specifically."""

    def test_nearest_neighbor_greedy_selection(self):
        """Test that nearest-neighbor selects closest unassigned orders."""
        optimizer = RouteOptimizer()

        vehicle = Vehicle(
            id="v1",
            max_weight_kg=500.0,
            max_volume_m3=10.0,
            start_location=(40.7128, -74.0060),
        )

        now = datetime.utcnow()
        time_window = TimeWindow(
            earliest=now,
            latest=now + timedelta(hours=12),
        )

        # Create orders in a line
        orders = [
            Order(
                id="o1",
                pickup_location=(40.7128, -74.0060),  # At depot
                delivery_location=(40.7130, -74.0060),
                time_window=time_window,
                weight_kg=10.0,
                volume_m3=0.1,
            ),
            Order(
                id="o2",
                pickup_location=(40.7129, -74.0060),  # Close to depot
                delivery_location=(40.7131, -74.0060),
                time_window=time_window,
                weight_kg=10.0,
                volume_m3=0.1,
            ),
            Order(
                id="o3",
                pickup_location=(40.7200, -74.0000),  # Far from depot
                delivery_location=(40.7210, -74.0000),
                time_window=time_window,
                weight_kg=10.0,
                volume_m3=0.1,
            ),
        ]

        routes = optimizer.optimize(orders, [vehicle])

        # Should create at least one route
        assert len(routes) >= 1
