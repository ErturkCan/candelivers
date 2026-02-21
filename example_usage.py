#!/usr/bin/env python
"""Example usage of CanDelivers optimization system."""

from datetime import datetime, timedelta
from services.routing.src.optimizer import RouteOptimizer, Order, Vehicle
from services.routing.src.constraints import TimeWindow
from packages.simulation.scenarios import ScenarioGenerator
from packages.simulation.metrics import MetricsCalculator


def example_basic_optimization():
    """Example: Basic route optimization."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Route Optimization")
    print("=" * 60)

    # Create optimizer
    optimizer = RouteOptimizer(use_distance_cache=False)

    # Define time window
    now = datetime.utcnow()
    time_window = TimeWindow(
        earliest=now,
        latest=now + timedelta(hours=12),
    )

    # Create orders
    orders = [
        Order(
            id="order_001",
            pickup_location=(40.7130, -74.0060),
            delivery_location=(40.7200, -74.0150),
            time_window=time_window,
            weight_kg=50.0,
            volume_m3=1.0,
        ),
        Order(
            id="order_002",
            pickup_location=(40.7140, -74.0070),
            delivery_location=(40.7210, -74.0160),
            time_window=time_window,
            weight_kg=75.0,
            volume_m3=1.5,
        ),
        Order(
            id="order_003",
            pickup_location=(40.7150, -74.0080),
            delivery_location=(40.7220, -74.0170),
            time_window=time_window,
            weight_kg=60.0,
            volume_m3=1.2,
        ),
    ]

    # Create vehicles
    vehicles = [
        Vehicle(
            id="vehicle_001",
            max_weight_kg=500.0,
            max_volume_m3=10.0,
            start_location=(40.7128, -74.0060),
        ),
    ]

    # Optimize routes
    routes = optimizer.optimize(orders, vehicles, improve_with_2opt=True)

    # Display results
    print(f"\nOptimized {len(orders)} orders with {len(vehicles)} vehicle(s)\n")

    for route in routes:
        print(f"Route: {route.vehicle_id}")
        print(f"  Orders: {route.stops}")
        print(f"  Total Distance: {route.total_distance:.2f} km")
        print(f"  Total Time: {route.total_time_minutes:.1f} minutes")
        print(f"  Weight Used: {route.weight_used:.1f} / {vehicles[0].max_weight_kg} kg")
        print(f"  Volume Used: {route.volume_used:.2f} / {vehicles[0].max_volume_m3} m³")


def example_capacity_constraints():
    """Example: Multiple vehicles with capacity constraints."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Capacity Constraints with Multiple Vehicles")
    print("=" * 60)

    optimizer = RouteOptimizer()

    now = datetime.utcnow()
    time_window = TimeWindow(
        earliest=now,
        latest=now + timedelta(hours=12),
    )

    # Heavy orders that need multiple vehicles
    orders = [
        Order(
            id=f"order_{i:03d}",
            pickup_location=(40.7128 + i * 0.002, -74.0060),
            delivery_location=(40.7200 + i * 0.002, -74.0150),
            time_window=time_window,
            weight_kg=120.0,
            volume_m3=2.0,
        )
        for i in range(5)
    ]

    # Multiple vehicles with limited capacity
    vehicles = [
        Vehicle(
            id=f"vehicle_{i:02d}",
            max_weight_kg=250.0,
            max_volume_m3=5.0,
            start_location=(40.7128, -74.0060),
        )
        for i in range(3)
    ]

    routes = optimizer.optimize(orders, vehicles, improve_with_2opt=True)

    print(f"\nOptimized {len(orders)} heavy orders with {len(vehicles)} vehicles\n")

    total_distance = 0
    total_weight = 0

    for route in routes:
        if route.stops:
            print(f"Route: {route.vehicle_id}")
            print(f"  Orders: {route.stops}")
            print(f"  Distance: {route.total_distance:.2f} km")
            print(f"  Weight: {route.weight_used:.1f} kg")
            print(f"  Volume: {route.volume_used:.2f} m³")
            total_distance += route.total_distance
            total_weight += route.weight_used

    print(f"\nTotal Distance: {total_distance:.2f} km")
    print(f"Total Weight: {total_weight:.1f} kg")


def example_scenario_generation():
    """Example: Generate and analyze a scenario."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Scenario Generation and Metrics")
    print("=" * 60)

    # Generate a medium-sized scenario
    scenario = ScenarioGenerator.scenario_medium_uniform()

    print(f"\nScenario Configuration:")
    print(f"  Orders: {scenario.num_orders}")
    print(f"  Vehicles: {scenario.num_vehicles}")
    print(f"  Time Distribution: {scenario.time_distribution.value}")
    print(f"  Size Distribution: {scenario.size_distribution.value}")
    print(f"  Simulation Duration: {scenario.simulation_hours} hours")

    # Generate orders and vehicles
    orders_data = ScenarioGenerator.generate_orders(
        scenario.num_orders,
        scenario.area_bounds,
        scenario.time_distribution,
        scenario.size_distribution,
        scenario.simulation_hours,
    )

    vehicles_data = ScenarioGenerator.generate_vehicles(
        scenario.num_vehicles,
        scenario.depot_location,
    )

    # Calculate statistics
    avg_weight = sum(o["weight_kg"] for o in orders_data) / len(orders_data)
    avg_volume = sum(o["volume_m3"] for o in orders_data) / len(orders_data)
    total_capacity_weight = sum(v["max_weight_kg"] for v in vehicles_data)
    total_capacity_volume = sum(v["max_volume_m3"] for v in vehicles_data)

    print(f"\nGenerated Orders Statistics:")
    print(f"  Average Weight: {avg_weight:.1f} kg")
    print(f"  Average Volume: {avg_volume:.2f} m³")
    print(f"  Total Orders Weight: {sum(o['weight_kg'] for o in orders_data):.1f} kg")
    print(f"  Total Orders Volume: {sum(o['volume_m3'] for o in orders_data):.2f} m³")

    print(f"\nFleet Capacity:")
    print(f"  Total Weight Capacity: {total_capacity_weight:.1f} kg")
    print(f"  Total Volume Capacity: {total_capacity_volume:.2f} m³")

    # Calculate utilization if we could pack perfectly
    total_weight = sum(o["weight_kg"] for o in orders_data)
    total_volume = sum(o["volume_m3"] for o in orders_data)
    weight_util = (total_weight / total_capacity_weight) * 100 if total_capacity_weight > 0 else 0
    volume_util = (total_volume / total_capacity_volume) * 100 if total_capacity_volume > 0 else 0

    print(f"\nTheoretical Utilization (perfect packing):")
    print(f"  Weight: {weight_util:.1f}%")
    print(f"  Volume: {volume_util:.1f}%")


def example_2opt_improvement():
    """Example: Demonstrate 2-opt improvement."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: 2-Opt Local Search Improvement")
    print("=" * 60)

    optimizer = RouteOptimizer()

    now = datetime.utcnow()
    time_window = TimeWindow(
        earliest=now,
        latest=now + timedelta(hours=12),
    )

    # Create orders in a line (worst initial ordering)
    orders = [
        Order(
            id=f"order_{i:03d}",
            pickup_location=(40.7128, -74.0060 + i * 0.001),
            delivery_location=(40.7200, -74.0150 + i * 0.001),
            time_window=time_window,
            weight_kg=30.0,
            volume_m3=0.5,
        )
        for i in range(5)
    ]

    vehicle = Vehicle(
        id="vehicle_001",
        max_weight_kg=500.0,
        max_volume_m3=10.0,
        start_location=(40.7128, -74.0060),
    )

    # Optimize without 2-opt
    routes_without_2opt = optimizer.optimize(orders, [vehicle], improve_with_2opt=False)
    distance_without = routes_without_2opt[0].total_distance if routes_without_2opt else 0

    # Optimize with 2-opt
    routes_with_2opt = optimizer.optimize(orders, [vehicle], improve_with_2opt=True)
    distance_with = routes_with_2opt[0].total_distance if routes_with_2opt else 0

    print(f"\nRoute Optimization Comparison:")
    print(f"  Without 2-Opt: {distance_without:.2f} km")
    print(f"  With 2-Opt:    {distance_with:.2f} km")

    if distance_without > 0:
        improvement = ((distance_without - distance_with) / distance_without) * 100
        print(f"  Improvement:   {improvement:.1f}%")


def example_metrics():
    """Example: Calculate and display metrics."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Performance Metrics")
    print("=" * 60)

    # Simulate some results
    metrics = MetricsCalculator.calculate_metrics(
        total_orders=100,
        completed_orders=98,
        failed_orders=2,
        order_delays=[2.5, 3.1, 1.8, 4.2, 0.5, 3.8, 2.9, 1.2],
        total_distance_km=450.0,
        total_vehicle_hours=42.0,
        vehicle_utilization={
            "vehicle_001": 82.5,
            "vehicle_002": 75.3,
            "vehicle_003": 88.1,
            "vehicle_004": 71.2,
            "vehicle_005": 79.8,
        },
        on_time_count=96,
    )

    # Print report
    report = MetricsCalculator.summary_report(metrics)
    print(report)


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("# CanDelivers Optimization System - Usage Examples")
    print("#" * 60)

    # Run examples
    example_basic_optimization()
    example_capacity_constraints()
    example_scenario_generation()
    example_2opt_improvement()
    example_metrics()

    print("\n" + "#" * 60)
    print("# Examples completed successfully!")
    print("#" * 60 + "\n")
