from enum import StrEnum


class Trend(StrEnum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    NEW = "NEW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


def determine_trend(recent_count: int, previous_count: int, total_count: int) -> Trend:
    if total_count < 3:
        return Trend.INSUFFICIENT_DATA
    if previous_count == 0 and recent_count > 0:
        return Trend.NEW
    if recent_count > previous_count * 1.2:
        return Trend.INCREASING
    if recent_count < previous_count * 0.8:
        return Trend.DECREASING
    return Trend.STABLE
