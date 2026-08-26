"""Stress/strain recovery and the interactive quick-look plot."""

from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go

from fem_engine.elements.quadrature import quadrature_rule
from fem_engine.elements.reference import (
    physical_shape_function_derivatives,
    shape_function_derivatives,
)
from fem_engine.kinematics import strain_displacement_matrix
from fem_engine.materials.base import Material, MaterialState
from fem_engine.mesh.schema import Mesh


@dataclass(frozen=True, slots=True)
class StressStrainField:
    node_strain: np.ndarray  # (n_nodes, 3): eps_xx, eps_yy, gamma_xy
    node_stress: np.ndarray  # (n_nodes, 3): sigma_xx, sigma_yy, tau_xy


def recover_stress_strain(
    mesh: Mesh, displacement: np.ndarray, material: Material
) -> StressStrainField:
    """Simple nodal averaging: each element contributes its Gauss-point-
    averaged strain/stress to each of its nodes; nodal values are then
    averaged over all elements sharing that node. Superconvergent patch
    recovery is a future, more accurate alternative -- swappable without
    touching assembly/solver.
    """
    n_nodes = mesh.nodes.shape[0]
    strain_sum = np.zeros((n_nodes, 3))
    stress_sum = np.zeros((n_nodes, 3))
    count = np.zeros(n_nodes)
    state = MaterialState()

    for element_type, connectivity in mesh.elements.items():
        points, _ = quadrature_rule(element_type)
        for element_nodes in connectivity:
            node_coords = mesh.nodes[element_nodes]
            dofs = np.empty(2 * len(element_nodes), dtype=int)
            dofs[0::2] = 2 * element_nodes
            dofs[1::2] = 2 * element_nodes + 1
            u_e = displacement[dofs]

            elem_strain = np.zeros(3)
            elem_stress = np.zeros(3)
            for xi, eta in points:
                dn_dnatural = shape_function_derivatives(element_type, xi, eta)
                dn_dx, _ = physical_shape_function_derivatives(node_coords, dn_dnatural)
                b = strain_displacement_matrix(dn_dx)
                strain = b @ u_e
                stress, _, _ = material.stress_and_tangent(strain, state)
                elem_strain += strain
                elem_stress += stress
            elem_strain /= len(points)
            elem_stress /= len(points)

            for node_id in element_nodes:
                strain_sum[node_id] += elem_strain
                stress_sum[node_id] += elem_stress
                count[node_id] += 1

    count = np.maximum(count, 1.0)
    return StressStrainField(
        node_strain=strain_sum / count[:, None],
        node_stress=stress_sum / count[:, None],
    )


def plot_result(
    mesh: Mesh,
    displacement: np.ndarray,
    field: StressStrainField,
    deflection_scale: float = 1.0,
) -> go.Figure:
    """Interactive quick-look: a toggle between undeflected and deflected
    (scaled) shapes, with hover tooltips showing per-node displacement,
    strain, and stress. For dev-loop/demo use alongside, not instead of,
    the VTU export.
    """
    n_nodes = mesh.nodes.shape[0]
    ux = displacement[0::2]
    uy = displacement[1::2]
    deflected = mesh.nodes + deflection_scale * np.column_stack([ux, uy])

    von_mises = np.sqrt(
        field.node_stress[:, 0] ** 2
        - field.node_stress[:, 0] * field.node_stress[:, 1]
        + field.node_stress[:, 1] ** 2
        + 3 * field.node_stress[:, 2] ** 2
    )

    hover_text = [
        f"node {i}<br>"
        f"u=({ux[i]:.4g}, {uy[i]:.4g})<br>"
        f"eps=({field.node_strain[i, 0]:.4g}, {field.node_strain[i, 1]:.4g}, "
        f"{field.node_strain[i, 2]:.4g})<br>"
        f"sigma=({field.node_stress[i, 0]:.4g}, {field.node_stress[i, 1]:.4g}, "
        f"{field.node_stress[i, 2]:.4g})<br>"
        f"von Mises={von_mises[i]:.4g}"
        for i in range(n_nodes)
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=mesh.nodes[:, 0],
            y=mesh.nodes[:, 1],
            mode="markers",
            name="undeflected",
            marker={"size": 6, "color": "lightgray"},
            text=hover_text,
            hoverinfo="text",
            visible=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=deflected[:, 0],
            y=deflected[:, 1],
            mode="markers",
            name="deflected",
            marker={
                "size": 6,
                "color": von_mises,
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": "von Mises"},
            },
            text=hover_text,
            hoverinfo="text",
            visible=False,
        )
    )
    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": 1.15,
                "buttons": [
                    {
                        "label": "Undeflected",
                        "method": "update",
                        "args": [{"visible": [True, False]}],
                    },
                    {
                        "label": "Deflected",
                        "method": "update",
                        "args": [{"visible": [False, True]}],
                    },
                ],
            }
        ],
        yaxis={"scaleanchor": "x", "scaleratio": 1},
        title="FEM result quick-look",
    )
    return fig
