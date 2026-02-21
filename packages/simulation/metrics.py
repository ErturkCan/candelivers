"""Simulation metrics calculation."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class SimulationMetrics:
    """Metrics for simulation results."""

    completion_rate: float  # 0-100, percentage of orders completed
    avg_delay_minutes: float  # Average delay from time window
    vehicle_utilization: Dict[str, float] = field(
        default_factory=dict
    )  # Vehicle ID -> utilization %
    cost_per_delivery: float = 0.0  # Cost per order delivered
    on_time_percentage: float = 0.0  # Percentage of on-time deliveries
    total_distance_km: float = 0.0
    total_vehicle_hours: float = 0.0
    avg_orders_per_vehicle: float = 0.0
    total_orders: int = 0
    completed_orders: int = 0
    failed_orders: int = 0


class MetricsCalculator:
    """Calculate simulation metrics."""

    COST_PER_KM = 1.50  # Cost per km
    COST_PER_HOUR = 20.0  # Cost per vehicle hour

    @staticmethod
    def calculate_metrics(
        total_orders: int,
        completed_orders: int,
        failed_orders: int,
        order_delays: List[float],
        total_distance_km: float,
        total_vehicle_hours: float,
        vehicle_utilization: Dict[str, float],
        on_time_count: int = None,
    ) -> SimulationMetrics:
        """Calculate metrics from simulation results.

        Args:
            total_orders: Total number of orders
            completed_orders: Number of completed orders
            failed_orders: Number of failed orders
            order_delays: List of delays in minutes for each order
            total_distance_km: Total distance traveled
            total_vehicle_hours: Total vehicle hours used
            vehicle_utilization: Dictionary of vehicle utilization
            on_time_count: Number of on-time deliveries

        Returns:
            Calculated metrics
        """
        if total_orders == 0:
            total_orders = completed_orders + failed_orders

        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        on_time_percentage = (
            (on_time_count / completed_orders * 100) if completed_orders > 0 else 0
        )

        avg_delay = 0.0
        if order_delays:
            avg_delay = sum(order_delays) / len(order_delays)

        # Calculate cost
        distance_cost = total_distance_km * MetricsCalculator.COST_PER_KM
        labor_cost = total_vehicle_hours * MetricsCalculator.COST_PER_HOUR
        total_cost = distance_cost + labor_cost
        cost_per_delivery = (
            (total_cost / completed_orders) if completed_orders > 0 else 0
        )

        # Average orders per vehicle
        num_vehicles = len(vehicle_utilization) if vehicle_utilization else 1
        avg_orders = (completed_orders / num_vehicles) if num_vehicles > 0 else 0

        return SimulationMetrics(
            completion_rate=round(completion_rate, 2),
            avg_delay_minutes=round(avg_delay, 2),
            vehicle_utilization=vehicle_utilization,
            cost_per_delivery=round(cost_per_delivery, 2),
            on_time_percentage=round(on_time_percentage, 2),
            total_distance_km=round(total_distance_km, 2),
            total_vehicle_hours=round(total_vehicle_hours, 2),
            avg_orders_per_vehicle=round(avg_orders, 2),
            total_orders=total_orders,
            completed_orders=completed_orders,
            failed_orders=failed_orders,
        )

    @staticmethod
    def calculate_vehicle_utilization(
        vehicle_capacity_weight: float,
        vehicle_capacity_volume: float,
        assigned_weight: float,
        assigned_volume: float,
    ) -> float:
        """Calculate vehicle utilization percentage.

        Args:
            vehicle_capacity_weight: Vehicle weight capacity
            vehicle_capacity_volume: Vehicle volume capacity
            assigned_weight: Assigned weight
            assigned_volume: Assigned volume

        Returns:
            Utilization percentage (0-100)
        """
        weight_util = (assigned_weight / vehicle_capacity_weight * 100) if vehicle_capacity_weight > 0 else 0
        volume_util = (assigned_volume / vehicle_capacity_volume * 100) if vehicle_capacity_volume > 0 else 0

        # Use average of both
        avg_util = (weight_util + volume_util) / 2
        return min(100, avg_util)  # Cap at 100%

    @staticmethod
    def summary_report(metrics: SimulationMetrics) -> str:
        """Generate a text summary of metrics.

        Args:
            metrics: SimulationMetrics object

        Returns:
            Formatted summary report
        """
        report = f"""
SIMULATION METRICS REPORT
{'=' * 50}
Orders Completed:         {metrics.completed_orders}/{metrics.total_orders} ({metrics.completion_rate}%)
Failed Orders:            {metrics.failed_orders}
On-Time Deliveries:       {metrics.on_time_percentage}%
Average Delay:            {metrics.avg_delay_minutes} minutes

OPERATIONAL METRICS
{'=' * 50}
Total Distance:           {metrics.total_distance_km} km
Total Vehicle Hours:      {metrics.total_vehicle_hours} hours
Avg Orders per Vehicle:   {metrics.avg_orders_per_vehicle}
Cost per Delivery:        ${metrics.cost_per_delivery}

VEHICLE UTILIZATION
{'=' * 50}
"""
        for vehicle_id, utilization in metrics.vehicle_utilization.items():
            report += f"{vehicle_id}: {utilization:.1f}%\n"

        return report
