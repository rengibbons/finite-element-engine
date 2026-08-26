"""Small-strain kinematics: the strain-displacement (B) operator.

Finite-strain kinematics (deformation gradient, Green-Lagrange strain) for
future large-deformation plasticity is a separate function added here later,
not a retrofit of this one.
"""

import numpy as np


def strain_displacement_matrix(dn_dx: np.ndarray) -> np.ndarray:
    """Builds the small-strain B-matrix from physical shape function
    derivatives.

    dn_dx: (n_nodes, 2) array of [dN/dx, dN/dy] per node.
    Returns B of shape (3, 2*n_nodes) such that strain = B @ u_element,
    with strain rows ordered [eps_xx, eps_yy, gamma_xy].
    """
    n_nodes = dn_dx.shape[0]
    b = np.zeros((3, 2 * n_nodes))
    b[0, 0::2] = dn_dx[:, 0]
    b[1, 1::2] = dn_dx[:, 1]
    b[2, 0::2] = dn_dx[:, 1]
    b[2, 1::2] = dn_dx[:, 0]
    return b
