"""Pydantic models for order service."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Tuple, Optional
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class TimeWindowModel(BaseModel):
    """Time window model."""

    earliest: datetime
    latest: datetime


class Order(BaseModel):
    """Order model."""

    id: str
    pickup_location: Tuple[float, float] = Field(..., description="(latitude, longitude)")
    delivery_location: Tuple[float, float] = Field(..., description="(latitude, longitude)")
    time_window: TimeWindowModel
    weight_kg: float = Field(..., gt=0)
    volume_m3: float = Field(..., gt=0)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_route_id: Optional[str] = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class Vehicle(BaseModel):
    """Vehicle model."""

    id: str
    max_weight_kg: float = Field(..., gt=0)
    max_volume_m3: float = Field(..., gt=0)
    start_location: Tuple[float, float] = Field(..., description="(latitude, longitude)")
    end_location: Optional[Tuple[float, float]] = Field(None, description="(latitude, longitude)")
    available: bool = True


class Stop(BaseModel):
    """Stop in a route."""

    order_id: str
    location: Tuple[float, float]
    arrival_time_minutes: int
    service_time_minutes: int


class Route(BaseModel):
    """Route model."""

    id: str
    vehicle_id: str
    stops: List[Stop]
    total_distance_km: float
    total_time_minutes: float
    weight_used_kg: float
    volume_used_m3: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizationRequest(BaseModel):
    """Request model for optimization."""

    orders: List[Order]
    vehicles: List[Vehicle]
    use_2opt: bool = True


class OptimizationResult(BaseModel):
    """Result model for optimization."""

    routes: List[Route]
    unassigned_orders: List[str]
    total_distance_km: float
    total_vehicle_hours: float
    optimization_time_seconds: float
    algorithm: str = "nearest_neighbor_2opt"

    class Config:
        """Pydantic config."""

        use_enum_values = True
