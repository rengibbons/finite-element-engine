"""Linear elastic material, plane stress or plane strain."""

from dataclasses import dataclass

import numpy as np

from fem_engine.materials.base import MaterialState
from fem_engine.types import PlaneCondition


@dataclass(frozen=True, slots=True)
class LinearElastic:
    young_modulus: float
    poisson_ratio: float
    plane_condition: PlaneCondition

    @property
    def lame_lambda(self) -> float:
        e, nu = self.young_modulus, self.poisson_ratio
        return e * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))

    @property
    def shear_modulus(self) -> float:
        return self.young_modulus / (2.0 * (1.0 + self.poisson_ratio))

    def constitutive_matrix(self) -> np.ndarray:
        """The 3x3 D matrix such that stress = D @ strain, for
        [eps_xx, eps_yy, gamma_xy] -> [sigma_xx, sigma_yy, tau_xy]."""
        e, nu = self.young_modulus, self.poisson_ratio
        if self.plane_condition == "plane_stress":
            factor = e / (1.0 - nu**2)
            return factor * np.array(
                [
                    [1.0, nu, 0.0],
                    [nu, 1.0, 0.0],
                    [0.0, 0.0, (1.0 - nu) / 2.0],
                ]
            )
        factor = e / ((1.0 + nu) * (1.0 - 2.0 * nu))
        return factor * np.array(
            [
                [1.0 - nu, nu, 0.0],
                [nu, 1.0 - nu, 0.0],
                [0.0, 0.0, (1.0 - 2.0 * nu) / 2.0],
            ]
        )

    def stress_and_tangent(
        self, strain: np.ndarray, state: MaterialState
    ) -> tuple[np.ndarray, np.ndarray, MaterialState]:
        d = self.constitutive_matrix()
        stress = d @ strain
        return stress, d, state
