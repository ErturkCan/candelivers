"""Constraint definitions and validation for routing."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class TimeWindow:
    """Time window constraint: earliest and latest delivery times."""

    earliest: datetime
    latest: datetime

    def contains(self, time: datetime) -> bool:
        """Check if time is within the window."""
        return self.earliest <= time <= self.latest

    def is_feasible(self, arrival_time: datetime) -> bool:
        """Check if arrival time is feasible for this window."""
        return arrival_time <= self.latest


class Constraint(ABC):
    """Base class for routing constraints."""

    @abstractmethod
    def validate(self, route: List[Tuple[int, int, float]]) -> bool:
        """Validate a route.

        Args:
            route: List of (location_id, time_minutes, cumulative_load)

        Returns:
            True if constraint is satisfied, False otherwise
        """
        pass


class VehicleCapacityConstraint(Constraint):
    """Validates weight and volume capacity constraints."""

    def __init__(self, max_weight_kg: float, max_volume_m3: float):
        """Initialize capacity constraint.

        Args:
            max_weight_kg: Maximum weight capacity in kg
            max_volume_m3: Maximum volume capacity in m³
        """
        self.max_weight_kg = max_weight_kg
        self.max_volume_m3 = max_volume_m3

    def validate(self, route_loads: List[Tuple[float, float]]) -> bool:
        """Validate that route loads don't exceed capacity.

        Args:
            route_loads: List of (weight_kg, volume_m3) tuples

        Returns:
            True if all loads are within capacity
        """
        total_weight = 0.0
        total_volume = 0.0

        for weight, volume in route_loads:
            total_weight += weight
            total_volume += volume

            if total_weight > self.max_weight_kg:
                return False
            if total_volume > self.max_volume_m3:
                return False

        return True


class TimeWindowConstraint(Constraint):
    """Validates time window constraints."""

    def __init__(self, service_time_minutes: int = 30):
        """Initialize time window constraint.

        Args:
            service_time_minutes: Service time at each location in minutes
        """
        self.service_time_minutes = service_time_minutes

    def validate(
        self,
        time_windows: List[TimeWindow],
        arrival_times: List[int],
        start_time: int = 0,
    ) -> bool:
        """Validate time window constraints for a route.

        Args:
            time_windows: List of TimeWindow objects
            arrival_times: List of arrival times in minutes from start
            start_time: Route start time in minutes (default 0)

        Returns:
            True if all arrivals are within time windows
        """
        for i, (tw, arrival_min) in enumerate(zip(time_windows, arrival_times)):
            arrival_time = start_time + arrival_min
            # Convert to minutes from midnight for comparison
            earliest_min = tw.earliest.hour * 60 + tw.earliest.minute
            latest_min = tw.latest.hour * 60 + tw.latest.minute

            # Allow for arrival within window (within a day)
            arrival_min_of_day = arrival_time % (24 * 60)
            if arrival_min_of_day > latest_min or arrival_min_of_day < earliest_min:
                return False

        return True


class DriverHoursConstraint(Constraint):
    """Validates driver hours and mandatory breaks."""

    def __init__(
        self,
        max_shift_hours: float = 10.0,
        mandatory_break_hours: float = 0.5,
        break_after_hours: float = 5.0,
    ):
        """Initialize driver hours constraint.

        Args:
            max_shift_hours: Maximum shift duration in hours
            mandatory_break_hours: Length of mandatory break in hours
            break_after_hours: Hours of driving before mandatory break required
        """
        self.max_shift_hours = max_shift_hours
        self.mandatory_break_hours = mandatory_break_hours
        self.break_after_hours = break_after_hours

    def validate(self, total_time_minutes: int, driving_time_minutes: int) -> bool:
        """Validate driver hours constraints.

        Args:
            total_time_minutes: Total route time in minutes
            driving_time_minutes: Total driving time in minutes

        Returns:
            True if driver hour constraints are satisfied
        """
        total_hours = total_time_minutes / 60.0
        driving_hours = driving_time_minutes / 60.0

        # Check max shift
        if total_hours > self.max_shift_hours:
            return False

        # Check if break is needed
        if driving_hours > self.break_after_hours:
            min_total_with_break = (
                driving_hours + self.mandatory_break_hours
            ) * 60
            if total_time_minutes < min_total_with_break:
                return False

        return True


class ZoneRestrictionConstraint(Constraint):
    """Validates geographic zone restrictions."""

    def __init__(self, excluded_zones: Set[str]):
        """Initialize zone restriction constraint.

        Args:
            excluded_zones: Set of zone IDs that are excluded
        """
        self.excluded_zones = excluded_zones

    def validate(self, zones: List[str]) -> bool:
        """Validate that no locations are in excluded zones.

        Args:
            zones: List of zone IDs for each location

        Returns:
            True if no zone is excluded
        """
        for zone in zones:
            if zone in self.excluded_zones:
                return False
        return True


class ConstraintChecker:
    """Checks multiple constraints for route validity."""

    def __init__(self):
        """Initialize constraint checker."""
        self.constraints: List[Constraint] = []

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the checker.

        Args:
            constraint: Constraint to add
        """
        self.constraints.append(constraint)

    def check_capacity(
        self, max_weight_kg: float, max_volume_m3: float, route_loads: List[Tuple[float, float]]
    ) -> bool:
        """Check capacity constraint.

        Args:
            max_weight_kg: Max weight in kg
            max_volume_m3: Max volume in m³
            route_loads: List of (weight, volume) tuples

        Returns:
            True if capacity is not exceeded
        """
        constraint = VehicleCapacityConstraint(max_weight_kg, max_volume_m3)
        return constraint.validate(route_loads)

    def check_time_windows(
        self,
        time_windows: List[TimeWindow],
        arrival_times: List[int],
        start_time: int = 0,
    ) -> bool:
        """Check time window constraints.

        Args:
            time_windows: List of TimeWindow objects
            arrival_times: List of arrival times in minutes
            start_time: Route start time in minutes

        Returns:
            True if all time windows are met
        """
        constraint = TimeWindowConstraint()
        return constraint.validate(time_windows, arrival_times, start_time)

    def check_driver_hours(
        self, total_time_minutes: int, driving_time_minutes: int
    ) -> bool:
        """Check driver hours constraints.

        Args:
            total_time_minutes: Total time in minutes
            driving_time_minutes: Driving time in minutes

        Returns:
            True if driver hour constraints are met
        """
        constraint = DriverHoursConstraint()
        return constraint.validate(total_time_minutes, driving_time_minutes)

    def check_zones(self, zones: List[str], excluded_zones: Set[str]) -> bool:
        """Check zone restrictions.

        Args:
            zones: List of zone IDs
            excluded_zones: Set of excluded zone IDs

        Returns:
            True if no excluded zones are visited
        """
        constraint = ZoneRestrictionConstraint(excluded_zones)
        return constraint.validate(zones)
