"""Reference-element shape functions, natural-coordinate derivatives, and the
isoparametric mapping to physical coordinates.

Adding a new element type (TRI6, QUAD8, TET4, HEX8, ...) means adding a
branch here and a matching entry in quadrature.py -- no other module needs
to change.
"""

from typing import cast

import numpy as np

from fem_engine.types import ElementType

_QUAD4_CORNER_XI = np.array([-1.0, 1.0, 1.0, -1.0])
_QUAD4_CORNER_ETA = np.array([-1.0, -1.0, 1.0, 1.0])


def shape_functions(element_type: ElementType, xi: float, eta: float) -> np.ndarray:
    """Shape function values N_i(xi, eta) at a natural-coordinate point.
    Returns an array of shape (n_nodes,)."""
    if element_type is ElementType.TRI3:
        return np.array([1.0 - xi - eta, xi, eta])
    if element_type is ElementType.QUAD4:
        return 0.25 * (1.0 + xi * _QUAD4_CORNER_XI) * (1.0 + eta * _QUAD4_CORNER_ETA)
    raise ValueError(f"Unsupported element type: {element_type}")


def shape_function_derivatives(
    element_type: ElementType, xi: float, eta: float
) -> np.ndarray:
    """Natural-coordinate derivatives dN_i/dxi, dN_i/deta at (xi, eta).
    Returns an array of shape (n_nodes, 2): columns [dN/dxi, dN/deta]."""
    if element_type is ElementType.TRI3:
        return np.array([[-1.0, -1.0], [1.0, 0.0], [0.0, 1.0]])
    if element_type is ElementType.QUAD4:
        dn_dxi = 0.25 * _QUAD4_CORNER_XI * (1.0 + eta * _QUAD4_CORNER_ETA)
        dn_deta = 0.25 * _QUAD4_CORNER_ETA * (1.0 + xi * _QUAD4_CORNER_XI)
        return np.column_stack([dn_dxi, dn_deta])
    raise ValueError(f"Unsupported element type: {element_type}")


def jacobian(node_coords: np.ndarray, dn_dnatural: np.ndarray) -> np.ndarray:
    """The 2x2 Jacobian d(x,y)/d(xi,eta) of the isoparametric map.

    node_coords: (n_nodes, 2) physical coordinates of the element's nodes.
    dn_dnatural: (n_nodes, 2) natural-coordinate shape function derivatives.
    """
    return cast(np.ndarray, node_coords.T @ dn_dnatural)


def physical_shape_function_derivatives(
    node_coords: np.ndarray, dn_dnatural: np.ndarray
) -> tuple[np.ndarray, float]:
    """Maps natural-coordinate shape function derivatives to physical
    (x, y) derivatives via the Jacobian, for use in the B-matrix.

    Returns (dN/dx,dN/dy of shape (n_nodes, 2), det(J)).
    """
    j = jacobian(node_coords, dn_dnatural)
    det_j = float(np.linalg.det(j))
    if det_j <= 0:
        raise ValueError(
            f"Non-positive Jacobian determinant ({det_j}); check element node "
            "ordering/orientation (should be counter-clockwise)."
        )
    dn_dphysical = dn_dnatural @ np.linalg.inv(j)
    return dn_dphysical, det_j
