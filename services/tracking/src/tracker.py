"""Vehicle tracking and ETA calculation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import math


@dataclass
class VehiclePosition:
    """Current vehicle position."""

    vehicle_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    speed_kmh: float = 40.0
    heading: float = 0.0


@dataclass
class StopInfo:
    """Information about a delivery stop."""

    order_id: str
    location: tuple  # (lat, lng)
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    status: str = "pending"  # pending, arrived, completed


class VehicleTracker:
    """Tracks vehicle positions and calculates ETAs."""

    EARTH_RADIUS_KM = 6371.0
    AVG_SPEED_KMH = 40.0
    SERVICE_TIME_MINUTES = 30

    def __init__(self):
        """Initialize vehicle tracker."""
        self.positions: Dict[str, VehiclePosition] = {}
        self.routes: Dict[str, List[StopInfo]] = {}
        self.callbacks: List[Callable] = []

    def update_position(self, position: VehiclePosition) -> None:
        """Update vehicle position.

        Args:
            position: Updated vehicle position
        """
        self.positions[position.vehicle_id] = position
        self._emit_event("position_updated", position)

    def register_route(self, vehicle_id: str, stops: List[StopInfo]) -> None:
        """Register a route for a vehicle.

        Args:
            vehicle_id: Vehicle identifier
            stops: List of delivery stops
        """
        self.routes[vehicle_id] = stops

    def get_position(self, vehicle_id: str) -> Optional[VehiclePosition]:
        """Get current position of a vehicle.

        Args:
            vehicle_id: Vehicle identifier

        Returns:
            Current position or None if not tracked
        """
        return self.positions.get(vehicle_id)

    def calculate_eta(self, vehicle_id: str) -> Optional[datetime]:
        """Calculate ETA for vehicle to complete all deliveries.

        Args:
            vehicle_id: Vehicle identifier

        Returns:
            Estimated completion time or None if no route
        """
        if vehicle_id not in self.routes:
            return None

        position = self.positions.get(vehicle_id)
        if not position:
            return None

        stops = self.routes[vehicle_id]
        if not stops:
            return None

        # Find next pending stop
        next_stop_idx = 0
        for i, stop in enumerate(stops):
            if stop.status == "pending":
                next_stop_idx = i
                break

        total_minutes = 0
        current_location = (position.latitude, position.longitude)

        # Calculate time to remaining stops
        for i in range(next_stop_idx, len(stops)):
            stop = stops[i]

            # Distance to this stop
            distance = self._haversine_distance(current_location, stop.location)

            # Travel time
            travel_minutes = (distance / self.AVG_SPEED_KMH) * 60

            total_minutes += travel_minutes + self.SERVICE_TIME_MINUTES

            current_location = stop.location

        return datetime.utcnow() + timedelta(minutes=total_minutes)

    def calculate_eta_to_stop(
        self, vehicle_id: str, order_id: str
    ) -> Optional[datetime]:
        """Calculate ETA to a specific stop.

        Args:
            vehicle_id: Vehicle identifier
            order_id: Order identifier

        Returns:
            Estimated arrival time or None if not found
        """
        if vehicle_id not in self.routes:
            return None

        position = self.positions.get(vehicle_id)
        if not position:
            return None

        stops = self.routes[vehicle_id]

        # Find the stop
        target_stop_idx = None
        for i, stop in enumerate(stops):
            if stop.order_id == order_id:
                target_stop_idx = i
                break

        if target_stop_idx is None:
            return None

        total_minutes = 0
        current_location = (position.latitude, position.longitude)

        # Calculate time to target stop
        for i in range(target_stop_idx + 1):
            stop = stops[i]

            # Distance to this stop
            distance = self._haversine_distance(current_location, stop.location)

            # Travel time
            travel_minutes = (distance / self.AVG_SPEED_KMH) * 60

            if i < target_stop_idx:
                total_minutes += travel_minutes + self.SERVICE_TIME_MINUTES
            else:
                total_minutes += travel_minutes

            current_location = stop.location

        return datetime.utcnow() + timedelta(minutes=total_minutes)

    def mark_stop_completed(self, vehicle_id: str, order_id: str) -> None:
        """Mark a stop as completed.

        Args:
            vehicle_id: Vehicle identifier
            order_id: Order identifier
        """
        if vehicle_id not in self.routes:
            return

        stops = self.routes[vehicle_id]
        for stop in stops:
            if stop.order_id == order_id:
                stop.status = "completed"
                stop.departure_time = datetime.utcnow()
                self._emit_event("stop_completed", (vehicle_id, order_id))
                break

    def mark_stop_arrived(self, vehicle_id: str, order_id: str) -> None:
        """Mark a stop as arrived.

        Args:
            vehicle_id: Vehicle identifier
            order_id: Order identifier
        """
        if vehicle_id not in self.routes:
            return

        stops = self.routes[vehicle_id]
        for stop in stops:
            if stop.order_id == order_id:
                stop.status = "arrived"
                stop.arrival_time = datetime.utcnow()
                self._emit_event("stop_arrived", (vehicle_id, order_id))
                break

    def get_vehicle_stops(self, vehicle_id: str) -> List[StopInfo]:
        """Get all stops for a vehicle.

        Args:
            vehicle_id: Vehicle identifier

        Returns:
            List of stops or empty list
        """
        return self.routes.get(vehicle_id, [])

    def register_callback(self, callback: Callable) -> None:
        """Register a callback for tracking events.

        Args:
            callback: Callback function that receives (event_type, data)
        """
        self.callbacks.append(callback)

    def _emit_event(self, event_type: str, data: any) -> None:
        """Emit a tracking event.

        Args:
            event_type: Type of event
            data: Event data
        """
        for callback in self.callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"Error in callback: {e}")

    @staticmethod
    def _haversine_distance(loc1: tuple, loc2: tuple) -> float:
        """Calculate distance between two points using Haversine formula.

        Args:
            loc1: (latitude, longitude) tuple
            loc2: (latitude, longitude) tuple

        Returns:
            Distance in kilometers
        """
        lat1, lng1 = loc1
        lat2, lng2 = loc2

        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)

        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return VehicleTracker.EARTH_RADIUS_KM * c
