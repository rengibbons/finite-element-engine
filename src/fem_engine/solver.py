"""Linear system solve (direct or CG) and, later, the Newton-Raphson driver
for nonlinear materials.
"""

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import cg, spsolve

from fem_engine.types import SolverMethod


def solve_linear(
    k: sp.csr_matrix,
    f: np.ndarray,
    dirichlet_dofs: np.ndarray,
    dirichlet_values: np.ndarray,
    method: SolverMethod = "direct",
) -> np.ndarray:
    """Solves K u = f subject to essential (Dirichlet) BCs via row/column
    elimination, then a direct sparse solve or conjugate gradient on the
    reduced free-DOF system.
    """
    n_dofs = f.shape[0]
    free_dofs = np.setdiff1d(np.arange(n_dofs), dirichlet_dofs)

    u = np.zeros(n_dofs)
    u[dirichlet_dofs] = dirichlet_values

    k_fd = k[free_dofs][:, dirichlet_dofs]
    f_reduced = f[free_dofs] - k_fd @ dirichlet_values
    k_reduced = k[free_dofs][:, free_dofs].tocsr()

    if method == "direct":
        u_free = spsolve(k_reduced, f_reduced)
    elif method == "cg":
        u_free, info = cg(k_reduced, f_reduced)
        if info != 0:
            raise RuntimeError(f"Conjugate gradient did not converge (info={info})")
    else:
        raise ValueError(f"Unsupported solver method: {method}")

    u[free_dofs] = u_free
    return u


def solve_nonlinear() -> np.ndarray:
    """Newton-Raphson driver for future nonlinear materials (plasticity,
    viscoelastoplasticity): an outer time/load-step loop, inner Newton
    iterations using the consistent tangent from Material.stress_and_tangent,
    each iteration resolving to solve_linear. Stubbed -- no nonlinear
    material exists yet to exercise it against.
    """
    raise NotImplementedError(
        "solve_nonlinear is a stub until a nonlinear material (e.g. Plastic) exists"
    )
