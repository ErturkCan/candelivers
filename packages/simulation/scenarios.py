"""Scenario generation for simulation."""

import random
from dataclasses import dataclass
from typing import List, Tuple, Callable
from enum import Enum
from datetime import datetime, timedelta


class TimeDistribution(str, Enum):
    """Time distribution types."""

    UNIFORM = "uniform"
    RUSH_HOUR = "rush_hour"
    EVENING = "evening"


class SizeDistribution(str, Enum):
    """Item size distribution types."""

    UNIFORM = "uniform"
    SMALL_HEAVY = "small_heavy"
    LARGE_LIGHT = "large_light"


@dataclass
class Scenario:
    """Scenario configuration."""

    num_orders: int
    num_vehicles: int
    area_bounds: Tuple[float, float, float, float]  # (min_lat, min_lng, max_lat, max_lng)
    time_distribution: TimeDistribution = TimeDistribution.UNIFORM
    size_distribution: SizeDistribution = SizeDistribution.UNIFORM
    simulation_hours: float = 12.0
    depot_location: Tuple[float, float] = (40.7128, -74.0060)  # Default: NYC


class ScenarioGenerator:
    """Generate configurable simulation scenarios."""

    @staticmethod
    def generate_orders(
        num_orders: int,
        area_bounds: Tuple[float, float, float, float],
        time_distribution: TimeDistribution = TimeDistribution.UNIFORM,
        size_distribution: SizeDistribution = SizeDistribution.UNIFORM,
        simulation_hours: float = 12.0,
    ) -> List[dict]:
        """Generate orders for simulation.

        Args:
            num_orders: Number of orders to generate
            area_bounds: Geographic bounds (min_lat, min_lng, max_lat, max_lng)
            time_distribution: Type of time distribution
            size_distribution: Type of size distribution
            simulation_hours: Hours in simulation

        Returns:
            List of order dictionaries
        """
        orders = []
        min_lat, min_lng, max_lat, max_lng = area_bounds
        simulation_minutes = simulation_hours * 60

        for i in range(num_orders):
            # Generate location
            pickup_lat = random.uniform(min_lat, max_lat)
            pickup_lng = random.uniform(min_lng, max_lng)
            delivery_lat = random.uniform(min_lat, max_lat)
            delivery_lng = random.uniform(min_lng, max_lng)

            # Generate arrival time
            if time_distribution == TimeDistribution.UNIFORM:
                arrival_time = random.uniform(0, simulation_minutes)
            elif time_distribution == TimeDistribution.RUSH_HOUR:
                # More orders between 8-10 AM and 5-7 PM
                hour = random.choice(
                    [random.uniform(8 * 60, 10 * 60), random.uniform(17 * 60, 19 * 60)]
                )
                arrival_time = hour
            else:  # EVENING
                arrival_time = random.uniform(17 * 60, 22 * 60)

            # Generate size
            if size_distribution == SizeDistribution.UNIFORM:
                weight = random.uniform(10, 100)
                volume = random.uniform(0.1, 2.0)
            elif size_distribution == SizeDistribution.SMALL_HEAVY:
                weight = random.uniform(50, 150)
                volume = random.uniform(0.1, 0.5)
            else:  # LARGE_LIGHT
                weight = random.uniform(5, 30)
                volume = random.uniform(1.0, 5.0)

            # Time window (2-hour delivery window starting from arrival)
            window_start = datetime.utcnow() + timedelta(minutes=arrival_time)
            window_end = window_start + timedelta(hours=2)

            orders.append(
                {
                    "id": f"order_{i:05d}",
                    "pickup_location": (pickup_lat, pickup_lng),
                    "delivery_location": (delivery_lat, delivery_lng),
                    "weight_kg": round(weight, 1),
                    "volume_m3": round(volume, 2),
                    "arrival_time_minutes": arrival_time,
                    "time_window_start": window_start,
                    "time_window_end": window_end,
                }
            )

        return orders

    @staticmethod
    def generate_vehicles(
        num_vehicles: int,
        depot_location: Tuple[float, float],
        max_weight_kg: float = 500.0,
        max_volume_m3: float = 10.0,
    ) -> List[dict]:
        """Generate vehicles for simulation.

        Args:
            num_vehicles: Number of vehicles to generate
            depot_location: Depot location (lat, lng)
            max_weight_kg: Maximum weight capacity
            max_volume_m3: Maximum volume capacity

        Returns:
            List of vehicle dictionaries
        """
        vehicles = []

        for i in range(num_vehicles):
            # Slight variation in capacities (±10%)
            weight = max_weight_kg * random.uniform(0.9, 1.1)
            volume = max_volume_m3 * random.uniform(0.9, 1.1)

            vehicles.append(
                {
                    "id": f"vehicle_{i:03d}",
                    "max_weight_kg": round(weight, 1),
                    "max_volume_m3": round(volume, 2),
                    "start_location": depot_location,
                    "end_location": depot_location,
                }
            )

        return vehicles

    @staticmethod
    def create_scenario(
        num_orders: int = 50,
        num_vehicles: int = 5,
        area_bounds: Tuple[float, float, float, float] = (40.70, -74.02, 40.72, -73.98),
        time_distribution: TimeDistribution = TimeDistribution.UNIFORM,
        size_distribution: SizeDistribution = SizeDistribution.UNIFORM,
        simulation_hours: float = 12.0,
        depot_location: Tuple[float, float] = (40.7128, -74.0060),
    ) -> Scenario:
        """Create a complete scenario.

        Args:
            num_orders: Number of orders
            num_vehicles: Number of vehicles
            area_bounds: Geographic bounds
            time_distribution: Time distribution type
            size_distribution: Size distribution type
            simulation_hours: Simulation duration
            depot_location: Depot location

        Returns:
            Scenario object
        """
        return Scenario(
            num_orders=num_orders,
            num_vehicles=num_vehicles,
            area_bounds=area_bounds,
            time_distribution=time_distribution,
            size_distribution=size_distribution,
            simulation_hours=simulation_hours,
            depot_location=depot_location,
        )

    @staticmethod
    def scenario_small_peak() -> Scenario:
        """Create a small scenario with peak hour distribution."""
        return ScenarioGenerator.create_scenario(
            num_orders=20,
            num_vehicles=3,
            time_distribution=TimeDistribution.RUSH_HOUR,
            size_distribution=SizeDistribution.SMALL_HEAVY,
        )

    @staticmethod
    def scenario_medium_uniform() -> Scenario:
        """Create a medium scenario with uniform distribution."""
        return ScenarioGenerator.create_scenario(
            num_orders=50,
            num_vehicles=5,
            time_distribution=TimeDistribution.UNIFORM,
            size_distribution=SizeDistribution.UNIFORM,
        )

    @staticmethod
    def scenario_large_evening() -> Scenario:
        """Create a large scenario with evening distribution."""
        return ScenarioGenerator.create_scenario(
            num_orders=100,
            num_vehicles=10,
            time_distribution=TimeDistribution.EVENING,
            size_distribution=SizeDistribution.LARGE_LIGHT,
        )
