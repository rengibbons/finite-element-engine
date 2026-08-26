"""Run configuration: TOML -> validated Pydantic model -> frozen dataclass.

Pydantic is used only at this I/O boundary (parsing/validating the TOML file
a user hands us). Everything downstream of `load_config` works with the
plain frozen dataclasses defined below, per the project's data-class
convention.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from fem_engine.types import PlaneCondition, SolverMethod

# --- Pydantic models (I/O boundary only) -----------------------------------


class _StrictModel(BaseModel):
    """Base for all config models: reject unknown keys so a typo in the TOML
    file fails loudly instead of being silently ignored."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class MeshModel(_StrictModel):
    path: Path


class MaterialModel(_StrictModel):
    model: Literal["linear_elastic"]
    young_modulus: float
    poisson_ratio: float

    @model_validator(mode="after")
    def _check_physical_bounds(self) -> "MaterialModel":
        if self.young_modulus <= 0:
            raise ValueError(
                f"young_modulus must be positive, got {self.young_modulus}"
            )
        if not (-1.0 < self.poisson_ratio < 0.5):
            raise ValueError(
                f"poisson_ratio must be in (-1, 0.5) for isotropic elastic "
                f"stability, got {self.poisson_ratio}"
            )
        return self


class AnalysisModel(_StrictModel):
    plane_condition: PlaneCondition
    thickness: float

    @model_validator(mode="after")
    def _check_thickness(self) -> "AnalysisModel":
        if self.thickness <= 0:
            raise ValueError(f"thickness must be positive, got {self.thickness}")
        return self


class EssentialBCModel(_StrictModel):
    ux: float | None = None
    uy: float | None = None

    @model_validator(mode="after")
    def _check_at_least_one_dof(self) -> "EssentialBCModel":
        if self.ux is None and self.uy is None:
            raise ValueError("essential BC must prescribe at least one of ux, uy")
        return self


class NaturalBCModel(_StrictModel):
    traction: tuple[float, float]


class BoundaryConditionsModel(_StrictModel):
    essential: dict[str, EssentialBCModel] = {}
    natural: dict[str, NaturalBCModel] = {}


class SolverModel(_StrictModel):
    method: SolverMethod = "direct"


class OutputModel(_StrictModel):
    dir: Path
    run_name: str | None = None


class RunConfigModel(_StrictModel):
    mesh: MeshModel
    material: MaterialModel
    analysis: AnalysisModel
    boundary_conditions: BoundaryConditionsModel
    solver: SolverModel = SolverModel()
    output: OutputModel


# --- Frozen dataclasses (internal data model) -------------------------------


@dataclass(frozen=True, slots=True)
class MeshSpec:
    path: Path


@dataclass(frozen=True, slots=True)
class MaterialSpec:
    model: Literal["linear_elastic"]
    young_modulus: float
    poisson_ratio: float


@dataclass(frozen=True, slots=True)
class AnalysisSpec:
    plane_condition: PlaneCondition
    thickness: float


@dataclass(frozen=True, slots=True)
class EssentialBC:
    ux: float | None
    uy: float | None


@dataclass(frozen=True, slots=True)
class NaturalBC:
    traction: tuple[float, float]


@dataclass(frozen=True, slots=True)
class BoundaryConditionsSpec:
    essential: dict[str, EssentialBC]
    natural: dict[str, NaturalBC]


@dataclass(frozen=True, slots=True)
class SolverSpec:
    method: SolverMethod


@dataclass(frozen=True, slots=True)
class OutputSpec:
    dir: Path
    run_name: str | None


@dataclass(frozen=True, slots=True)
class RunConfig:
    mesh: MeshSpec
    material: MaterialSpec
    analysis: AnalysisSpec
    boundary_conditions: BoundaryConditionsSpec
    solver: SolverSpec
    output: OutputSpec


# --- Loader ------------------------------------------------------------------


def load_config(path: Path) -> RunConfig:
    """Read, validate, and convert a TOML run-config file into a `RunConfig`.

    Raises `tomllib.TOMLDecodeError` on malformed TOML and
    `pydantic.ValidationError` on a schema/value violation.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    validated = RunConfigModel.model_validate(raw)
    return _to_run_config(validated)


def _to_run_config(model: RunConfigModel) -> RunConfig:
    return RunConfig(
        mesh=MeshSpec(path=model.mesh.path),
        material=MaterialSpec(
            model=model.material.model,
            young_modulus=model.material.young_modulus,
            poisson_ratio=model.material.poisson_ratio,
        ),
        analysis=AnalysisSpec(
            plane_condition=model.analysis.plane_condition,
            thickness=model.analysis.thickness,
        ),
        boundary_conditions=BoundaryConditionsSpec(
            essential={
                name: EssentialBC(ux=bc.ux, uy=bc.uy)
                for name, bc in model.boundary_conditions.essential.items()
            },
            natural={
                name: NaturalBC(traction=bc.traction)
                for name, bc in model.boundary_conditions.natural.items()
            },
        ),
        solver=SolverSpec(method=model.solver.method),
        output=OutputSpec(dir=model.output.dir, run_name=model.output.run_name),
    )
