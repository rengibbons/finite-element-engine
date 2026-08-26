"""Orchestrates a full run: config -> mesh -> material -> assembly ->
boundary conditions -> solve -> post-process -> output.
"""

import logging
from pathlib import Path

from fem_engine.assembly import assemble_global
from fem_engine.boundary_conditions import dirichlet_dofs_and_values, natural_bc_forces
from fem_engine.config import load_config
from fem_engine.materials.linear_elastic import LinearElastic
from fem_engine.mesh.io import read_gmsh
from fem_engine.output import resolve_run_dir, write_outputs
from fem_engine.postprocess import recover_stress_strain
from fem_engine.solver import solve_linear

logger = logging.getLogger(__name__)


def run(config_path: Path) -> Path:
    config = load_config(config_path)
    run_dir = resolve_run_dir(config.output)
    run_dir.mkdir(parents=True, exist_ok=True)
    _setup_logging(run_dir)

    logger.info("Loaded config from %s", config_path)

    mesh = read_gmsh(config.mesh.path)
    logger.info("Loaded mesh: %d nodes", mesh.nodes.shape[0])

    material = LinearElastic(
        young_modulus=config.material.young_modulus,
        poisson_ratio=config.material.poisson_ratio,
        plane_condition=config.analysis.plane_condition,
    )

    k, f = assemble_global(mesh, material, config.analysis.thickness)
    f = f + natural_bc_forces(
        mesh, config.boundary_conditions.natural, config.analysis.thickness
    )
    dirichlet_dofs, dirichlet_values = dirichlet_dofs_and_values(
        mesh, config.boundary_conditions.essential
    )

    logger.info("Solving %d-DOF system", f.shape[0])
    displacement = solve_linear(
        k, f, dirichlet_dofs, dirichlet_values, method=config.solver.method
    )

    field = recover_stress_strain(mesh, displacement, material)

    write_outputs(run_dir, mesh, displacement, field, config_path)
    logger.info("Wrote outputs to %s", run_dir)
    return run_dir


def _setup_logging(run_dir: Path) -> None:
    file_handler = logging.FileHandler(run_dir / "run.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    )
    logging.basicConfig(
        level=logging.INFO, handlers=[logging.StreamHandler(), file_handler]
    )
