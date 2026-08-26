"""Structured mesh generator for the hello-world case -- no external mesh
tool required to get started.
"""

import numpy as np

from fem_engine.mesh.schema import Mesh
from fem_engine.types import ElementType


def generate_rectangle(
    width: float,
    height: float,
    n_x: int,
    n_y: int,
    element_type: ElementType,
) -> Mesh:
    """A structured grid over [0, width] x [0, height].

    n_x, n_y: number of elements along each axis.
    Boundary groups: "left", "right", "bottom", "top".
    """
    xs = np.linspace(0.0, width, n_x + 1)
    ys = np.linspace(0.0, height, n_y + 1)
    xx, yy = np.meshgrid(xs, ys, indexing="xy")
    nodes = np.column_stack([xx.ravel(), yy.ravel()])

    def node_id(i: int, j: int) -> int:
        return j * (n_x + 1) + i

    quads = []
    for j in range(n_y):
        for i in range(n_x):
            quads.append(
                [
                    node_id(i, j),
                    node_id(i + 1, j),
                    node_id(i + 1, j + 1),
                    node_id(i, j + 1),
                ]
            )
    quads_arr = np.array(quads, dtype=int)

    elements: dict[ElementType, np.ndarray]
    if element_type is ElementType.QUAD4:
        elements = {ElementType.QUAD4: quads_arr}
    elif element_type is ElementType.TRI3:
        tris = []
        for n0, n1, n2, n3 in quads_arr:
            tris.append([n0, n1, n2])
            tris.append([n0, n2, n3])
        elements = {ElementType.TRI3: np.array(tris, dtype=int)}
    else:
        raise ValueError(f"Unsupported element type: {element_type}")

    def edge_group(node_ids: list[int]) -> np.ndarray:
        return np.array(
            [[node_ids[k], node_ids[k + 1]] for k in range(len(node_ids) - 1)],
            dtype=int,
        )

    boundary_edges = {
        "left": edge_group([node_id(0, j) for j in range(n_y + 1)]),
        "right": edge_group([node_id(n_x, j) for j in range(n_y + 1)]),
        "bottom": edge_group([node_id(i, 0) for i in range(n_x + 1)]),
        "top": edge_group([node_id(i, n_y) for i in range(n_x + 1)]),
    }

    return Mesh(nodes=nodes, elements=elements, boundary_edges=boundary_edges)
