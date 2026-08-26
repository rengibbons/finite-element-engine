"""Resolves named boundary-condition groups (from config) against a Mesh's
boundary_edges into DOF indices/values (essential) or a force vector
(natural). Actual elimination happens in solver.py.
"""

import numpy as np

from fem_engine.assembly import element_force_traction
from fem_engine.config import EssentialBC, NaturalBC
from fem_engine.mesh.schema import Mesh


def dirichlet_dofs_and_values(
    mesh: Mesh, essential: dict[str, EssentialBC]
) -> tuple[np.ndarray, np.ndarray]:
    """Resolves named essential BC groups into global DOF indices and their
    prescribed values, for use by solver.solve_linear."""
    dofs: list[int] = []
    values: list[float] = []
    for group_name, bc in essential.items():
        edges = mesh.boundary_edges[group_name]
        node_ids = np.unique(edges.ravel())
        for node_id in node_ids:
            if bc.ux is not None:
                dofs.append(2 * int(node_id))
                values.append(bc.ux)
            if bc.uy is not None:
                dofs.append(2 * int(node_id) + 1)
                values.append(bc.uy)
    return np.array(dofs, dtype=int), np.array(values, dtype=float)


def natural_bc_forces(
    mesh: Mesh, natural: dict[str, NaturalBC], thickness: float
) -> np.ndarray:
    """Resolves named natural BC groups into a global nodal force vector."""
    n_dofs = 2 * mesh.nodes.shape[0]
    f = np.zeros(n_dofs)
    for group_name, bc in natural.items():
        edges = mesh.boundary_edges[group_name]
        for edge in edges:
            edge_node_coords = mesh.nodes[edge]
            f_e = element_force_traction(edge_node_coords, bc.traction, thickness)
            dofs = np.array(
                [2 * edge[0], 2 * edge[0] + 1, 2 * edge[1], 2 * edge[1] + 1]
            )
            f[dofs] += f_e
    return f
