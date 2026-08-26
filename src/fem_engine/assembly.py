"""Element-level and global stiffness/force assembly.

Global assembly is sparse throughout (scipy.sparse), never a dense matrix.
"""

import numpy as np
import scipy.sparse as sp

from fem_engine.elements.quadrature import quadrature_rule
from fem_engine.elements.reference import (
    physical_shape_function_derivatives,
    shape_function_derivatives,
)
from fem_engine.kinematics import strain_displacement_matrix
from fem_engine.materials.base import Material, MaterialState
from fem_engine.mesh.schema import Mesh
from fem_engine.types import ElementType


def element_stiffness(
    element_type: ElementType,
    node_coords: np.ndarray,
    material: Material,
    thickness: float,
) -> np.ndarray:
    """Element stiffness matrix Ke = integral(B^T D B t) dV via quadrature.

    node_coords: (n_nodes, 2). Returns (2*n_nodes, 2*n_nodes).

    Evaluated with zero strain: valid because the tangent D for a linear
    elastic material doesn't depend on strain. A future nonlinear material's
    residual/tangent assembly (in solve_nonlinear) calls
    material.stress_and_tangent with the actual current strain per Newton
    iteration instead -- this function's job is strictly the linear
    stiffness path.
    """
    n_nodes = node_coords.shape[0]
    k_e = np.zeros((2 * n_nodes, 2 * n_nodes))
    points, weights = quadrature_rule(element_type)
    state = MaterialState()
    zero_strain = np.zeros(3)

    for (xi, eta), w in zip(points, weights, strict=True):
        dn_dnatural = shape_function_derivatives(element_type, xi, eta)
        dn_dx, det_j = physical_shape_function_derivatives(node_coords, dn_dnatural)
        b = strain_displacement_matrix(dn_dx)
        _, d, _ = material.stress_and_tangent(zero_strain, state)
        k_e += (b.T @ d @ b) * det_j * w * thickness

    return k_e


def element_force_traction(
    edge_node_coords: np.ndarray,
    traction: tuple[float, float],
    thickness: float,
) -> np.ndarray:
    """Equivalent nodal forces from a constant traction on a 2-node
    (linear) edge.

    edge_node_coords: (2, 2), the two edge endpoints. Returns force vector
    of shape (4,) = [fx1, fy1, fx2, fy2] -- a constant traction on a linear
    edge splits evenly between its two nodes.
    """
    edge_length = float(np.linalg.norm(edge_node_coords[1] - edge_node_coords[0]))
    nodal_force = np.array(traction) * edge_length * thickness / 2.0
    return np.concatenate([nodal_force, nodal_force])


def _element_dofs(element_nodes: np.ndarray) -> np.ndarray:
    dofs = np.empty(2 * len(element_nodes), dtype=int)
    dofs[0::2] = 2 * element_nodes
    dofs[1::2] = 2 * element_nodes + 1
    return dofs


def assemble_global(
    mesh: Mesh, material: Material, thickness: float
) -> tuple[sp.csr_matrix, np.ndarray]:
    """Assembles the global sparse stiffness matrix and a zero force vector
    (natural BC forces are added separately by boundary_conditions.py).
    """
    n_dofs = 2 * mesh.nodes.shape[0]
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []

    for element_type, connectivity in mesh.elements.items():
        for element_nodes in connectivity:
            node_coords = mesh.nodes[element_nodes]
            k_e = element_stiffness(element_type, node_coords, material, thickness)
            dofs = _element_dofs(element_nodes)
            for local_i, global_i in enumerate(dofs):
                for local_j, global_j in enumerate(dofs):
                    rows.append(int(global_i))
                    cols.append(int(global_j))
                    data.append(k_e[local_i, local_j])

    k = sp.coo_matrix(
        (np.array(data), (np.array(rows), np.array(cols))), shape=(n_dofs, n_dofs)
    ).tocsr()
    f = np.zeros(n_dofs)
    return k, f
