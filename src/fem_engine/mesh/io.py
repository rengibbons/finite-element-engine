"""Reads a Gmsh .msh file into a Mesh via meshio."""

from pathlib import Path

import meshio
import numpy as np

from fem_engine.mesh.schema import Mesh
from fem_engine.types import ElementType

_MESHIO_TO_ELEMENT_TYPE = {
    "triangle": ElementType.TRI3,
    "quad": ElementType.QUAD4,
}


def read_gmsh(path: Path) -> Mesh:
    """Reads a Gmsh .msh file. Physical groups tagged on line (edge)
    elements become named boundary_edges groups, referenced by config
    boundary conditions."""
    raw = meshio.read(path)
    nodes = raw.points[:, :2]

    elements: dict[ElementType, np.ndarray] = {}
    for cell_block in raw.cells:
        if cell_block.type in _MESHIO_TO_ELEMENT_TYPE:
            elements[_MESHIO_TO_ELEMENT_TYPE[cell_block.type]] = cell_block.data

    boundary_edges: dict[str, list[np.ndarray]] = {}
    physical_names = (
        {int(tag_and_dim[0]): name for name, tag_and_dim in raw.field_data.items()}
        if raw.field_data
        else {}
    )
    physical_ids_per_block = raw.cell_data.get("gmsh:physical", [])
    for cell_block, physical_ids in zip(raw.cells, physical_ids_per_block, strict=True):
        if cell_block.type != "line":
            continue
        for physical_id in np.unique(physical_ids):
            group_name = physical_names.get(int(physical_id), str(int(physical_id)))
            mask = physical_ids == physical_id
            boundary_edges.setdefault(group_name, []).append(cell_block.data[mask])

    merged_boundary_edges = {
        name: np.concatenate(edge_arrays, axis=0)
        for name, edge_arrays in boundary_edges.items()
    }

    return Mesh(nodes=nodes, elements=elements, boundary_edges=merged_boundary_edges)
