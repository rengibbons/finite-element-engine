"""The Material interface every constitutive model implements.

This is the seam future viscoelastic, plastic, and viscoelastoplastic
models attach to without changing assembly, the solver, or post-processing:
they carry history in `state` and are otherwise called the same way.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True, slots=True)
class MaterialState:
    """Empty base state for history-independent materials. Inelastic models
    subclass this to carry internal/history variables (e.g. plastic strain,
    a hardening variable, viscous internal strains)."""


class Material(Protocol):
    def stress_and_tangent(
        self, strain: np.ndarray, state: MaterialState
    ) -> tuple[np.ndarray, np.ndarray, MaterialState]:
        """Given engineering strain [eps_xx, eps_yy, gamma_xy] and the
        material's current internal state, returns
        (stress [sigma_xx, sigma_yy, tau_xy], tangent (3x3), new_state)."""
        ...
