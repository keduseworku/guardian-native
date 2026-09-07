import math
from fractions import Fraction
from itertools import zip_longest


def weighted_mean(values, weights):
    missing = object()
    total_weight = Fraction()
    weighted_total = Fraction()
    seen = False

    for value, weight in zip_longest(values, weights, fillvalue=missing):
        if value is missing or weight is missing:
            raise ValueError("values and weights must have equal lengths")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or isinstance(weight, bool)
            or not isinstance(weight, (int, float))
        ):
            raise TypeError("values and weights must contain only int or float")
        if (
            (isinstance(value, float) and not math.isfinite(value))
            or (isinstance(weight, float) and not math.isfinite(weight))
        ):
            raise ValueError("values and weights must be finite")
        if weight < 0:
            raise ValueError("weights must be nonnegative")

        exact_weight = Fraction(weight)
        total_weight += exact_weight
        weighted_total += Fraction(value) * exact_weight
        seen = True

    if not seen:
        raise ValueError("values and weights must not be empty")
    if not total_weight:
        raise ValueError("weights must not all be zero")
    return float(weighted_total / total_weight)
