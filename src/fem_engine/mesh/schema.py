"""The Mesh data schema shared by mesh I/O, generation, and everything
downstream (elements, assembly, boundary conditions, post-processing)."""

from dataclasses import dataclass

import numpy as np

from fem_engine.types import ElementType


@dataclass(frozen=True, slots=True)
class Mesh:
    """A 2D finite element mesh.

    nodes: (n_nodes, 2) float array of node coordinates.
    elements: element type -> connectivity, (n_elements_of_type, nodes_per_element)
        int array of node indices into `nodes`.
    boundary_edges: physical/named group -> (n_edges, 2) int array of node-index
        pairs. Essential BCs use the unique node set of a group; natural BCs
        use the edges directly for the traction integral. A single schema
        covers both so a boundary is defined once, not twice.
    """

    nodes: np.ndarray
    elements: dict[ElementType, np.ndarray]
    boundary_edges: dict[str, np.ndarray]
