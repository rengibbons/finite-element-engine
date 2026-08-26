"""Gauss quadrature rules, keyed by element type."""

import numpy as np

from fem_engine.types import ElementType

_TRI3_POINTS = np.array([[1.0 / 3.0, 1.0 / 3.0]])
_TRI3_WEIGHTS = np.array([0.5])

_A = 1.0 / np.sqrt(3.0)
_QUAD4_POINTS = np.array([[-_A, -_A], [_A, -_A], [_A, _A], [-_A, _A]])
_QUAD4_WEIGHTS = np.array([1.0, 1.0, 1.0, 1.0])


def quadrature_rule(element_type: ElementType) -> tuple[np.ndarray, np.ndarray]:
    """Gauss points and weights for an element type.

    Returns (points of shape (n_gauss_points, 2) as (xi, eta),
    weights of shape (n_gauss_points,)).
    """
    if element_type is ElementType.TRI3:
        return _TRI3_POINTS, _TRI3_WEIGHTS
    if element_type is ElementType.QUAD4:
        return _QUAD4_POINTS, _QUAD4_WEIGHTS
    raise ValueError(f"Unsupported element type: {element_type}")
