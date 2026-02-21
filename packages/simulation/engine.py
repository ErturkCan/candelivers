"""Discrete-event simulation engine."""

import heapq
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import random


class EventType(str, Enum):
    """Event types for simulation."""

    ORDER_ARRIVAL = "order_arrival"
    PICKUP_START = "pickup_start"
    PICKUP_END = "pickup_end"
    DELIVERY_START = "delivery_start"
    DELIVERY_END = "delivery_end"
    VEHICLE_AVAILABLE = "vehicle_available"
    OPTIMIZATION_TRIGGER = "optimization_trigger"
    SIMULATION_END = "simulation_end"


@dataclass
class Event:
    """Simulation event."""

    time: float  # Simulation time in minutes
    event_type: EventType
    entity_id: str  # Order ID, vehicle ID, etc.
    data: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """Comparison for heap ordering."""
        return self.time < other.time


@dataclass
class SimulationState:
    """Current simulation state."""

    current_time: float = 0.0
    orders_created: int = 0
    orders_completed: int = 0
    orders_failed: int = 0
    total_distance: float = 0.0
    total_wait_time: float = 0.0
    vehicle_utilization: Dict[str, float] = field(default_factory=dict)
    order_delays: List[float] = field(default_factory=list)


class SimulationEngine:
    """Discrete-event simulation engine for delivery system."""

    def __init__(self, random_seed: Optional[int] = None):
        """Initialize simulation engine.

        Args:
            random_seed: Seed for random number generation (for reproducibility)
        """
        if random_seed is not None:
            random.seed(random_seed)

        self.event_queue: List[Event] = []
        self.state = SimulationState()
        self.callbacks: Dict[EventType, List[Callable]] = {}
        self.random_seed = random_seed

    def schedule_event(self, event: Event) -> None:
        """Schedule an event.

        Args:
            event: Event to schedule
        """
        heapq.heappush(self.event_queue, event)

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Callback function(event) -> None
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)

    def _dispatch_event(self, event: Event) -> None:
        """Dispatch an event to subscribers.

        Args:
            event: Event to dispatch
        """
        if event.event_type in self.callbacks:
            for callback in self.callbacks[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in callback for {event.event_type}: {e}")

    def run(self, end_time: float) -> SimulationState:
        """Run simulation until end time.

        Args:
            end_time: Simulation end time in minutes

        Returns:
            Final simulation state
        """
        self.state.current_time = 0.0

        # Schedule initial events if queue is empty
        if not self.event_queue:
            self.schedule_event(
                Event(
                    time=end_time,
                    event_type=EventType.SIMULATION_END,
                    entity_id="system",
                )
            )

        # Process events
        while self.event_queue:
            event = heapq.heappop(self.event_queue)

            if event.time > end_time:
                break

            self.state.current_time = event.time
            self._dispatch_event(event)

        return self.state

    def add_order_arrival(
        self, time: float, order_id: str, location: tuple, weight: float, volume: float
    ) -> None:
        """Schedule an order arrival.

        Args:
            time: Arrival time in minutes
            order_id: Order identifier
            location: Delivery location (lat, lng)
            weight: Weight in kg
            volume: Volume in m³
        """
        event = Event(
            time=time,
            event_type=EventType.ORDER_ARRIVAL,
            entity_id=order_id,
            data={"location": location, "weight": weight, "volume": volume},
        )
        self.schedule_event(event)

    def add_pickup_event(
        self, time: float, order_id: str, vehicle_id: str, location: tuple
    ) -> None:
        """Schedule a pickup event.

        Args:
            time: Pickup time in minutes
            order_id: Order identifier
            vehicle_id: Vehicle identifier
            location: Pickup location (lat, lng)
        """
        # Start event
        event = Event(
            time=time,
            event_type=EventType.PICKUP_START,
            entity_id=order_id,
            data={"vehicle_id": vehicle_id, "location": location},
        )
        self.schedule_event(event)

        # End event (15 minutes service time)
        end_event = Event(
            time=time + 15,
            event_type=EventType.PICKUP_END,
            entity_id=order_id,
            data={"vehicle_id": vehicle_id},
        )
        self.schedule_event(end_event)

    def add_delivery_event(
        self, time: float, order_id: str, vehicle_id: str, location: tuple
    ) -> None:
        """Schedule a delivery event.

        Args:
            time: Delivery time in minutes
            order_id: Order identifier
            vehicle_id: Vehicle identifier
            location: Delivery location (lat, lng)
        """
        # Start event
        event = Event(
            time=time,
            event_type=EventType.DELIVERY_START,
            entity_id=order_id,
            data={"vehicle_id": vehicle_id, "location": location},
        )
        self.schedule_event(event)

        # End event (30 minutes service time)
        end_event = Event(
            time=time + 30,
            event_type=EventType.DELIVERY_END,
            entity_id=order_id,
            data={"vehicle_id": vehicle_id},
        )
        self.schedule_event(end_event)

    def get_state(self) -> SimulationState:
        """Get current simulation state.

        Returns:
            Current state
        """
        return self.state

    def reset(self) -> None:
        """Reset simulation state."""
        self.state = SimulationState()
        self.event_queue = []
        if self.random_seed is not None:
            random.seed(self.random_seed)
