"""Distance matrix computation using Haversine formula."""

import math
from typing import List, Tuple, Optional
import numpy as np


class DistanceMatrix:
    """Compute and cache distance matrices between locations."""

    EARTH_RADIUS_KM = 6371.0

    def __init__(self, use_cache: bool = False):
        """Initialize distance matrix.

        Args:
            use_cache: Whether to cache computed distance matrices
        """
        self.use_cache = use_cache
        self._cache: dict = {}

    @staticmethod
    def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
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

        return DistanceMatrix.EARTH_RADIUS_KM * c

    def compute_distance_matrix(
        self, locations: List[Tuple[float, float]]
    ) -> np.ndarray:
        """Compute distance matrix for a list of locations.

        Args:
            locations: List of (latitude, longitude) tuples

        Returns:
            NxN distance matrix where matrix[i][j] is distance from location i to j
        """
        cache_key = tuple(locations)
        if self.use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        n = len(locations)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                lat1, lng1 = locations[i]
                lat2, lng2 = locations[j]
                distance = self.haversine(lat1, lng1, lat2, lng2)
                matrix[i][j] = distance
                matrix[j][i] = distance

        if self.use_cache:
            self._cache[cache_key] = matrix

        return matrix

    def distance_between(
        self, loc1: Tuple[float, float], loc2: Tuple[float, float]
    ) -> float:
        """Get distance between two locations.

        Args:
            loc1: (latitude, longitude) tuple
            loc2: (latitude, longitude) tuple

        Returns:
            Distance in kilometers
        """
        return self.haversine(loc1[0], loc1[1], loc2[0], loc2[1])

    def bounding_box_query(
        self, locations: List[Tuple[float, float]], center: Tuple[float, float],
        radius_km: float
    ) -> List[int]:
        """Find locations within bounding box of given radius.

        Args:
            locations: List of (latitude, longitude) tuples
            center: Center point (latitude, longitude)
            radius_km: Search radius in kilometers

        Returns:
            List of indices of locations within radius
        """
        # Rough approximation: 1 degree latitude ≈ 111 km
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * math.cos(math.radians(center[0])))

        result = []
        for i, (lat, lng) in enumerate(locations):
            if (
                abs(lat - center[0]) <= lat_delta
                and abs(lng - center[1]) <= lng_delta
            ):
                result.append(i)

        return result

    def clear_cache(self) -> None:
        """Clear the distance cache."""
        self._cache.clear()
