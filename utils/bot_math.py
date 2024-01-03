import math
from math import pi
from sc2.position import Point2
from typing import List


def points_on_circumference(center: Point2, radius, n=10) -> List[Point2]:
    """Calculates all points on the circumference of a circle. n = number of points."""
    points = [
        (center.x + (math.cos(2 * pi / n * x) * radius), center.y + (math.sin(2 * pi / n * x) * radius))  # x  # y
        for x in range(0, n)
    ]

    point2list = list(map(lambda t: Point2(t), points))
    return point2list


def points_on_circumference_sorted(center: Point2, closest_to: Point2, radius, n=10) -> List[Point2]:
    """Calculates all points on the circumference of a circle, and sorts the points so that first one
    on the list has the shortest distance to closest_to parameter."""
    points = points_on_circumference(center, radius, n)

    closest_point = closest_to.closest(points)
    closest_point_index = points.index(closest_point)

    sorted_points = []

    # Points from the closest point to the end
    sorted_points.extend(points[closest_point_index:])

    # Points from start of list to the closest point (closest point not included)
    sorted_points.extend(points[0:closest_point_index])

    return sorted_points
