"""Geocoding utilities and spatial indexing."""

import math
from typing import List, Tuple, Dict, Set
from collections import defaultdict


class GeoUtils:
    """Geographic utility functions."""

    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def haversine_distance(
        lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula.

        Args:
            lat1: Latitude of first point (degrees)
            lng1: Longitude of first point (degrees)
            lat2: Latitude of second point (degrees)
            lng2: Longitude of second point (degrees)

        Returns:
            Distance in kilometers
        """
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

        return GeoUtils.EARTH_RADIUS_KM * c

    @staticmethod
    def bounding_box(
        center_lat: float, center_lng: float, radius_km: float
    ) -> Tuple[float, float, float, float]:
        """Get bounding box for a radius around a point.

        Args:
            center_lat: Center latitude
            center_lng: Center longitude
            radius_km: Radius in kilometers

        Returns:
            (min_lat, min_lng, max_lat, max_lng) tuple
        """
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))

        return (
            center_lat - lat_delta,
            center_lng - lng_delta,
            center_lat + lat_delta,
            center_lng + lng_delta,
        )

    @staticmethod
    def points_in_radius(
        center: Tuple[float, float],
        radius_km: float,
        points: List[Tuple[float, float]],
    ) -> List[Tuple[int, float]]:
        """Find points within a radius of a center point.

        Args:
            center: Center point (lat, lng)
            radius_km: Search radius in kilometers
            points: List of points (lat, lng)

        Returns:
            List of (index, distance) tuples for points within radius
        """
        result = []
        center_lat, center_lng = center

        for i, (lat, lng) in enumerate(points):
            distance = GeoUtils.haversine_distance(
                center_lat, center_lng, lat, lng
            )
            if distance <= radius_km:
                result.append((i, distance))

        return result


class GridIndex:
    """Grid-based spatial indexing for efficient location queries."""

    def __init__(self, cell_size_km: float = 1.0):
        """Initialize grid index.

        Args:
            cell_size_km: Size of each grid cell in kilometers
        """
        self.cell_size_km = cell_size_km
        self.grid: Dict[Tuple[int, int], List[Tuple[int, Tuple[float, float]]]] = (
            defaultdict(list)
        )

    def _get_cell_key(self, lat: float, lng: float) -> Tuple[int, int]:
        """Get grid cell key for a location.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            (cell_x, cell_y) tuple
        """
        # Each degree of latitude ≈ 111 km
        cell_y = int(lat / (self.cell_size_km / 111.0))
        # Each degree of longitude varies by latitude
        cell_x = int(lng / (self.cell_size_km / (111.0 * math.cos(math.radians(lat)))))

        return (cell_x, cell_y)

    def add_point(self, index: int, location: Tuple[float, float]) -> None:
        """Add a point to the index.

        Args:
            index: Point identifier
            location: (latitude, longitude) tuple
        """
        lat, lng = location
        cell_key = self._get_cell_key(lat, lng)
        self.grid[cell_key].append((index, location))

    def add_points(self, locations: List[Tuple[float, float]]) -> None:
        """Add multiple points to the index.

        Args:
            locations: List of (latitude, longitude) tuples
        """
        for i, location in enumerate(locations):
            self.add_point(i, location)

    def query_radius(
        self, center: Tuple[float, float], radius_km: float
    ) -> List[Tuple[int, float]]:
        """Query points within a radius.

        Args:
            center: Center point (lat, lng)
            radius_km: Search radius in kilometers

        Returns:
            List of (index, distance) tuples
        """
        result = []
        center_lat, center_lng = center

        # Get bounding box of cells to check
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        min_cell_lat = int((center_lat - lat_delta) / (self.cell_size_km / 111.0))
        max_cell_lat = int((center_lat + lat_delta) / (self.cell_size_km / 111.0))
        min_cell_lng = int((center_lng - lng_delta) / (self.cell_size_km / (111.0 * math.cos(math.radians(center_lat)))))
        max_cell_lng = int((center_lng + lng_delta) / (self.cell_size_km / (111.0 * math.cos(math.radians(center_lat)))))

        # Check all cells in bounding box
        for cell_y in range(min_cell_lat, max_cell_lat + 1):
            for cell_x in range(min_cell_lng, max_cell_lng + 1):
                cell_key = (cell_x, cell_y)
                if cell_key in self.grid:
                    for point_idx, location in self.grid[cell_key]:
                        distance = GeoUtils.haversine_distance(
                            center_lat, center_lng, location[0], location[1]
                        )
                        if distance <= radius_km:
                            result.append((point_idx, distance))

        return result

    def query_bounding_box(
        self, bounds: Tuple[float, float, float, float]
    ) -> List[Tuple[int, Tuple[float, float]]]:
        """Query points within a bounding box.

        Args:
            bounds: (min_lat, min_lng, max_lat, max_lng) tuple

        Returns:
            List of (index, location) tuples
        """
        result = []
        min_lat, min_lng, max_lat, max_lng = bounds

        # Get cell range
        min_cell_lat = int(min_lat / (self.cell_size_km / 111.0))
        max_cell_lat = int(max_lat / (self.cell_size_km / 111.0))
        min_cell_lng = int(min_lng / (self.cell_size_km / (111.0 * math.cos(math.radians(min_lat)))))
        max_cell_lng = int(max_lng / (self.cell_size_km / (111.0 * math.cos(math.radians(min_lat)))))

        # Check all cells
        for cell_y in range(min_cell_lat, max_cell_lat + 1):
            for cell_x in range(min_cell_lng, max_cell_lng + 1):
                cell_key = (cell_x, cell_y)
                if cell_key in self.grid:
                    for point_idx, location in self.grid[cell_key]:
                        lat, lng = location
                        if (
                            min_lat <= lat <= max_lat
                            and min_lng <= lng <= max_lng
                        ):
                            result.append((point_idx, location))

        return result

    def clear(self) -> None:
        """Clear the index."""
        self.grid.clear()
