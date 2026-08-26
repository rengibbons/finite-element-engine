"""Writes a self-contained run directory: raw arrays (npz, source of truth),
VTU (ParaView), an interactive Plotly HTML quick-look, a copy of the config
that produced the run, and (via run.py's logging setup) run.log.

All writes go through write_outputs so a later local-to-cloud-storage swap
(e.g. via fsspec) is a contained change rather than a rewrite.
"""

import shutil
from datetime import UTC, datetime
from pathlib import Path

import meshio
import numpy as np

from fem_engine.config import OutputSpec
from fem_engine.mesh.schema import Mesh
from fem_engine.postprocess import StressStrainField, plot_result
from fem_engine.types import ElementType

_MESHIO_CELL_NAME = {
    ElementType.TRI3: "triangle",
    ElementType.QUAD4: "quad",
}


def resolve_run_dir(output: OutputSpec) -> Path:
    """{run_name}_{timestamp} if run_name is set, else just {timestamp}
    (UTC) -- reruns never collide, even with an explicit run_name."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"{output.run_name}_{timestamp}" if output.run_name else timestamp
    return output.dir / name


def write_outputs(
    run_dir: Path,
    mesh: Mesh,
    displacement: np.ndarray,
    field: StressStrainField,
    config_path: Path,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)

    arrays: dict[str, np.ndarray] = {
        "nodes": mesh.nodes,
        "displacement": displacement,
        "node_strain": field.node_strain,
        "node_stress": field.node_stress,
    }
    for element_type, connectivity in mesh.elements.items():
        arrays[f"connectivity_{element_type.value}"] = connectivity
    # mypy can't statically rule out `allow_pickle` being a key of `arrays`
    # against savez's keyword-only bool param -- a known stub limitation
    # with **dict unpacking, not a real type error.
    np.savez(run_dir / "result.npz", **arrays)  # type: ignore[arg-type]

    cells = [
        (_MESHIO_CELL_NAME[element_type], connectivity)
        for element_type, connectivity in mesh.elements.items()
    ]
    ux = displacement[0::2]
    uy = displacement[1::2]
    vtu_mesh = meshio.Mesh(
        points=mesh.nodes,
        cells=cells,
        point_data={
            "displacement": np.column_stack([ux, uy]),
            "strain": field.node_strain,
            "stress": field.node_stress,
        },
    )
    meshio.write(run_dir / "result.vtu", vtu_mesh)

    fig = plot_result(mesh, displacement, field)
    fig.write_html(run_dir / "result.html")

    shutil.copy(config_path, run_dir / "config.toml")
