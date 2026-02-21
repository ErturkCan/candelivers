"""Tests for constraint validation."""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add src directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.routing.src.constraints import (
    VehicleCapacityConstraint,
    TimeWindowConstraint,
    DriverHoursConstraint,
    ZoneRestrictionConstraint,
    ConstraintChecker,
    TimeWindow,
)


class TestVehicleCapacityConstraint:
    """Test vehicle capacity constraint."""

    def test_empty_route_passes(self):
        """Test that empty route passes capacity check."""
        constraint = VehicleCapacityConstraint(
            max_weight_kg=500.0, max_volume_m3=10.0
        )
        assert constraint.validate([]) is True

    def test_within_capacity_passes(self):
        """Test route within capacity passes."""
        constraint = VehicleCapacityConstraint(
            max_weight_kg=500.0, max_volume_m3=10.0
        )
        route_loads = [(100.0, 2.0), (150.0, 3.0), (100.0, 2.0)]
        assert constraint.validate(route_loads) is True

    def test_exceed_weight_fails(self):
        """Test route exceeding weight capacity fails."""
        constraint = VehicleCapacityConstraint(
            max_weight_kg=300.0, max_volume_m3=10.0
        )
        route_loads = [(100.0, 2.0), (150.0, 3.0), (100.0, 2.0)]
        assert constraint.validate(route_loads) is False

    def test_exceed_volume_fails(self):
        """Test route exceeding volume capacity fails."""
        constraint = VehicleCapacityConstraint(
            max_weight_kg=500.0, max_volume_m3=5.0
        )
        route_loads = [(100.0, 2.0), (150.0, 3.0), (100.0, 2.0)]
        assert constraint.validate(route_loads) is False

    def test_exactly_at_capacity_passes(self):
        """Test route at exact capacity passes."""
        constraint = VehicleCapacityConstraint(
            max_weight_kg=300.0, max_volume_m3=7.0
        )
        route_loads = [(100.0, 2.0), (100.0, 2.5), (100.0, 2.5)]
        assert constraint.validate(route_loads) is True


class TestTimeWindowConstraint:
    """Test time window constraint."""

    def test_arrival_within_window_passes(self):
        """Test arrival within time window passes."""
        constraint = TimeWindowConstraint()

        now = datetime.utcnow()
        morning = now.replace(hour=8, minute=0)
        evening = now.replace(hour=18, minute=0)

        time_windows = [
            TimeWindow(earliest=morning, latest=evening),
            TimeWindow(earliest=morning, latest=evening),
        ]

        # Arrival times within window (in minutes of day)
        arrival_times = [500, 600]  # 8:20 AM, 10:00 AM

        assert constraint.validate(time_windows, arrival_times) is True

    def test_arrival_after_window_fails(self):
        """Test arrival after time window fails."""
        constraint = TimeWindowConstraint()

        now = datetime.utcnow()
        morning = now.replace(hour=8, minute=0)
        evening = now.replace(hour=18, minute=0)

        time_windows = [TimeWindow(earliest=morning, latest=evening)]

        # Arrival time after window (in minutes of day)
        arrival_times = [1200]  # 8:00 PM (20:00)

        assert constraint.validate(time_windows, arrival_times) is False

    def test_arrival_before_window_fails(self):
        """Test arrival before time window fails."""
        constraint = TimeWindowConstraint()

        now = datetime.utcnow()
        morning = now.replace(hour=8, minute=0)
        evening = now.replace(hour=18, minute=0)

        time_windows = [TimeWindow(earliest=morning, latest=evening)]

        # Arrival time before window (in minutes of day)
        arrival_times = [300]  # 5:00 AM

        assert constraint.validate(time_windows, arrival_times) is False


class TestDriverHoursConstraint:
    """Test driver hours constraint."""

    def test_short_shift_passes(self):
        """Test short shift within limits passes."""
        constraint = DriverHoursConstraint(
            max_shift_hours=10.0, break_after_hours=5.0
        )
        # 4 hours total, 3 hours driving
        assert constraint.validate(240, 180) is True

    def test_exceed_max_shift_fails(self):
        """Test exceeding max shift fails."""
        constraint = DriverHoursConstraint(
            max_shift_hours=10.0, break_after_hours=5.0
        )
        # 12 hours total (exceeds max of 10)
        assert constraint.validate(720, 600) is False

    def test_long_drive_without_break_fails(self):
        """Test long drive without break fails."""
        constraint = DriverHoursConstraint(
            max_shift_hours=10.0,
            mandatory_break_hours=0.5,
            break_after_hours=5.0,
        )
        # 5.5 hours driving without break (needs break after 5 hours)
        # Should fail because not enough time for break
        result = constraint.validate(300, 330)
        # Total is only 5 hours but driving is 5.5 - this is a special case
        assert result is False

    def test_long_drive_with_break_passes(self):
        """Test long drive with break passes."""
        constraint = DriverHoursConstraint(
            max_shift_hours=10.0,
            mandatory_break_hours=0.5,
            break_after_hours=5.0,
        )
        # 5 hours driving + 0.5 hour break + 1 hour return = 6.5 hours total
        assert constraint.validate(390, 300) is True


class TestZoneRestrictionConstraint:
    """Test zone restriction constraint."""

    def test_allowed_zones_pass(self):
        """Test allowed zones pass."""
        constraint = ZoneRestrictionConstraint(excluded_zones={"restricted_zone"})
        zones = ["zone_a", "zone_b", "zone_c"]
        assert constraint.validate(zones) is True

    def test_excluded_zones_fail(self):
        """Test excluded zones fail."""
        constraint = ZoneRestrictionConstraint(excluded_zones={"restricted_zone"})
        zones = ["zone_a", "restricted_zone", "zone_c"]
        assert constraint.validate(zones) is False

    def test_multiple_excluded_zones(self):
        """Test multiple excluded zones."""
        constraint = ZoneRestrictionConstraint(
            excluded_zones={"zone_a", "zone_b"}
        )
        zones = ["zone_c", "zone_d", "zone_e"]
        assert constraint.validate(zones) is True

        zones = ["zone_c", "zone_a", "zone_e"]
        assert constraint.validate(zones) is False


class TestConstraintChecker:
    """Test constraint checker."""

    def test_capacity_check(self):
        """Test capacity constraint checking."""
        checker = ConstraintChecker()

        assert (
            checker.check_capacity(
                max_weight_kg=500.0,
                max_volume_m3=10.0,
                route_loads=[(100.0, 2.0), (200.0, 4.0)],
            )
            is True
        )

        assert (
            checker.check_capacity(
                max_weight_kg=200.0,
                max_volume_m3=10.0,
                route_loads=[(100.0, 2.0), (200.0, 4.0)],
            )
            is False
        )

    def test_driver_hours_check(self):
        """Test driver hours constraint checking."""
        checker = ConstraintChecker()

        assert checker.check_driver_hours(total_time_minutes=300, driving_time_minutes=200) is True

        assert checker.check_driver_hours(total_time_minutes=720, driving_time_minutes=600) is False

    def test_zone_check(self):
        """Test zone restriction constraint checking."""
        checker = ConstraintChecker()

        assert (
            checker.check_zones(
                zones=["zone_a", "zone_b"],
                excluded_zones={"restricted"},
            )
            is True
        )

        assert (
            checker.check_zones(
                zones=["zone_a", "restricted"],
                excluded_zones={"restricted"},
            )
            is False
        )
