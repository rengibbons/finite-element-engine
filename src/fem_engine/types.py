"""Shared type aliases used across module boundaries.

Kept separate from any one module (config, materials, ...) so that modules
which both need these types don't have to import one another.
"""

from enum import Enum
from typing import Literal

PlaneCondition = Literal["plane_stress", "plane_strain"]
SolverMethod = Literal["direct", "cg"]


class ElementType(Enum):
    """Supported element types. Add table entries in elements/reference.py
    and elements/quadrature.py to extend, e.g. TRI6, QUAD8, TET4, HEX8."""

    TRI3 = "tri3"
    QUAD4 = "quad4"
