"""Tests for simulation engine and scenarios."""

import pytest
import sys
import os

# Add src directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from packages.simulation.engine import SimulationEngine, Event, EventType
from packages.simulation.scenarios import ScenarioGenerator, TimeDistribution, SizeDistribution
from packages.simulation.metrics import SimulationMetrics, MetricsCalculator


class TestSimulationEngine:
    """Test simulation engine."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        engine = SimulationEngine()
        assert engine is not None
        assert engine.state.current_time == 0.0
        assert engine.state.orders_created == 0

    def test_schedule_event(self):
        """Test event scheduling."""
        engine = SimulationEngine()
        event = Event(
            time=100.0,
            event_type=EventType.ORDER_ARRIVAL,
            entity_id="order_1",
        )
        engine.schedule_event(event)
        assert len(engine.event_queue) > 0

    def test_event_processing_in_order(self):
        """Test events are processed in time order."""
        engine = SimulationEngine()

        processed_times = []

        def callback(event):
            processed_times.append(event.time)

        engine.subscribe(EventType.ORDER_ARRIVAL, callback)

        # Schedule events out of order
        engine.schedule_event(
            Event(
                time=300.0,
                event_type=EventType.ORDER_ARRIVAL,
                entity_id="order_3",
            )
        )
        engine.schedule_event(
            Event(
                time=100.0,
                event_type=EventType.ORDER_ARRIVAL,
                entity_id="order_1",
            )
        )
        engine.schedule_event(
            Event(
                time=200.0,
                event_type=EventType.ORDER_ARRIVAL,
                entity_id="order_2",
            )
        )

        engine.run(end_time=500.0)

        # Check events were processed in order
        assert processed_times == [100.0, 200.0, 300.0]

    def test_simulation_determinism_with_seed(self):
        """Test simulation produces same results with same seed."""
        seed = 42

        # First run
        engine1 = SimulationEngine(random_seed=seed)
        for i in range(5):
            engine1.add_order_arrival(
                time=float(i * 60),
                order_id=f"order_{i}",
                location=(40.7128 + i * 0.001, -74.0060),
                weight=50.0,
                volume=1.0,
            )

        state1 = engine1.run(end_time=1000.0)

        # Second run with same seed
        engine2 = SimulationEngine(random_seed=seed)
        for i in range(5):
            engine2.add_order_arrival(
                time=float(i * 60),
                order_id=f"order_{i}",
                location=(40.7128 + i * 0.001, -74.0060),
                weight=50.0,
                volume=1.0,
            )

        state2 = engine2.run(end_time=1000.0)

        # States should match
        assert state1.current_time == state2.current_time

    def test_event_subscription(self):
        """Test event subscription works."""
        engine = SimulationEngine()

        events_received = []

        def callback(event):
            events_received.append(event)

        engine.subscribe(EventType.ORDER_ARRIVAL, callback)

        event = Event(
            time=50.0,
            event_type=EventType.ORDER_ARRIVAL,
            entity_id="order_1",
        )
        engine.schedule_event(event)
        engine.run(end_time=100.0)

        assert len(events_received) == 1
        assert events_received[0].entity_id == "order_1"

    def test_simulation_state_tracking(self):
        """Test simulation state is tracked correctly."""
        engine = SimulationEngine()

        def callback(event):
            if event.event_type == EventType.ORDER_ARRIVAL:
                engine.state.orders_created += 1

        engine.subscribe(EventType.ORDER_ARRIVAL, callback)

        for i in range(3):
            engine.add_order_arrival(
                time=float(i * 100),
                order_id=f"order_{i}",
                location=(40.7128, -74.0060),
                weight=50.0,
                volume=1.0,
            )

        engine.run(end_time=500.0)

        assert engine.state.orders_created == 3


class TestScenarioGenerator:
    """Test scenario generation."""

    def test_generate_orders(self):
        """Test order generation."""
        orders = ScenarioGenerator.generate_orders(
            num_orders=10,
            area_bounds=(40.70, -74.02, 40.72, -73.98),
            time_distribution=TimeDistribution.UNIFORM,
            size_distribution=SizeDistribution.UNIFORM,
        )

        assert len(orders) == 10

        for order in orders:
            assert "id" in order
            assert "pickup_location" in order
            assert "delivery_location" in order
            assert "weight_kg" in order
            assert "volume_m3" in order
            assert order["weight_kg"] > 0
            assert order["volume_m3"] > 0

    def test_generate_vehicles(self):
        """Test vehicle generation."""
        vehicles = ScenarioGenerator.generate_vehicles(
            num_vehicles=5,
            depot_location=(40.7128, -74.0060),
        )

        assert len(vehicles) == 5

        for vehicle in vehicles:
            assert "id" in vehicle
            assert "max_weight_kg" in vehicle
            assert "max_volume_m3" in vehicle
            assert "start_location" in vehicle
            assert vehicle["max_weight_kg"] > 0
            assert vehicle["max_volume_m3"] > 0

    def test_scenario_generation(self):
        """Test complete scenario generation."""
        scenario = ScenarioGenerator.create_scenario(
            num_orders=20,
            num_vehicles=3,
        )

        assert scenario.num_orders == 20
        assert scenario.num_vehicles == 3
        assert scenario.simulation_hours == 12.0

    def test_preset_scenarios(self):
        """Test preset scenario generators."""
        small_peak = ScenarioGenerator.scenario_small_peak()
        assert small_peak.num_orders == 20
        assert small_peak.num_vehicles == 3
        assert small_peak.time_distribution == TimeDistribution.RUSH_HOUR

        medium = ScenarioGenerator.scenario_medium_uniform()
        assert medium.num_orders == 50
        assert medium.num_vehicles == 5
        assert medium.time_distribution == TimeDistribution.UNIFORM

        large = ScenarioGenerator.scenario_large_evening()
        assert large.num_orders == 100
        assert large.num_vehicles == 10
        assert large.time_distribution == TimeDistribution.EVENING

    def test_time_distribution_affects_generation(self):
        """Test that time distribution affects order generation."""
        uniform_orders = ScenarioGenerator.generate_orders(
            num_orders=50,
            area_bounds=(40.70, -74.02, 40.72, -73.98),
            time_distribution=TimeDistribution.UNIFORM,
        )

        rush_orders = ScenarioGenerator.generate_orders(
            num_orders=50,
            area_bounds=(40.70, -74.02, 40.72, -73.98),
            time_distribution=TimeDistribution.RUSH_HOUR,
        )

        # Both should generate orders
        assert len(uniform_orders) == 50
        assert len(rush_orders) == 50

    def test_size_distribution_affects_generation(self):
        """Test that size distribution affects order generation."""
        uniform_sizes = ScenarioGenerator.generate_orders(
            num_orders=50,
            area_bounds=(40.70, -74.02, 40.72, -73.98),
            size_distribution=SizeDistribution.UNIFORM,
        )

        heavy_sizes = ScenarioGenerator.generate_orders(
            num_orders=50,
            area_bounds=(40.70, -74.02, 40.72, -73.98),
            size_distribution=SizeDistribution.SMALL_HEAVY,
        )

        # Calculate average weights
        avg_uniform = sum(o["weight_kg"] for o in uniform_sizes) / 50
        avg_heavy = sum(o["weight_kg"] for o in heavy_sizes) / 50

        # Heavy distribution should have higher average weight
        assert avg_heavy > avg_uniform


class TestSimulationMetrics:
    """Test metrics calculation."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = SimulationMetrics(
            completion_rate=100.0,
            avg_delay_minutes=5.0,
            on_time_percentage=95.0,
            total_distance_km=150.0,
            total_vehicle_hours=12.0,
        )

        assert metrics.completion_rate == 100.0
        assert metrics.avg_delay_minutes == 5.0

    def test_metrics_calculation(self):
        """Test metrics calculation."""
        metrics = MetricsCalculator.calculate_metrics(
            total_orders=100,
            completed_orders=95,
            failed_orders=5,
            order_delays=[5.0, 10.0, 3.0, 8.0, 2.0],
            total_distance_km=500.0,
            total_vehicle_hours=50.0,
            vehicle_utilization={"v1": 85.0, "v2": 70.0},
            on_time_count=90,
        )

        assert metrics.completion_rate == 95.0
        assert metrics.total_orders == 100
        assert metrics.completed_orders == 95
        assert metrics.failed_orders == 5
        assert metrics.on_time_percentage == 94.74  # 90/95 * 100

    def test_vehicle_utilization_calculation(self):
        """Test vehicle utilization calculation."""
        utilization = MetricsCalculator.calculate_vehicle_utilization(
            vehicle_capacity_weight=500.0,
            vehicle_capacity_volume=10.0,
            assigned_weight=450.0,
            assigned_volume=8.0,
        )

        # Weight util: 450/500 = 90%, Volume util: 8/10 = 80%, Avg = 85%
        assert 84.0 <= utilization <= 86.0

    def test_metrics_summary_report(self):
        """Test metrics summary report generation."""
        metrics = SimulationMetrics(
            completion_rate=95.0,
            avg_delay_minutes=5.5,
            vehicle_utilization={"v1": 85.0},
            on_time_percentage=90.0,
            total_distance_km=500.0,
            total_vehicle_hours=50.0,
            total_orders=100,
            completed_orders=95,
            failed_orders=5,
        )

        report = MetricsCalculator.summary_report(metrics)

        assert "SIMULATION METRICS REPORT" in report
        assert "95" in report  # completion rate
        assert "95" in report  # completed orders
        assert "500" in report  # distance

    def test_cost_per_delivery_calculation(self):
        """Test cost per delivery calculation."""
        metrics = MetricsCalculator.calculate_metrics(
            total_orders=100,
            completed_orders=100,
            failed_orders=0,
            order_delays=[],
            total_distance_km=1000.0,  # 1000 * 1.50 = 1500
            total_vehicle_hours=100.0,  # 100 * 20 = 2000
            vehicle_utilization={},
            on_time_count=100,
        )

        # Total cost = 1500 + 2000 = 3500, per delivery = 3500/100 = 35.0
        assert metrics.cost_per_delivery == 35.0
