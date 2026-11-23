"""Beam statics and serviceability calculations.

The public API uses feet and kips for beam loads and geometry. Section
properties use inches, ksi, and kip/in**2 internally where appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

SupportType = Literal["simply_supported", "cantilever"]


@dataclass(frozen=True)
class PointLoad:
    position_ft: float
    magnitude_kip: float


@dataclass(frozen=True)
class UniformLoad:
    start_ft: float
    end_ft: float
    magnitude_kip_per_ft: float


@dataclass(frozen=True)
class SectionProperties:
    name: str
    E_ksi: float
    I_in4: float
    S_in3: float
    allowable_stress_ksi: float


@dataclass(frozen=True)
class BeamInput:
    span_ft: float
    support_type: SupportType
    section: SectionProperties
    point_loads: tuple[PointLoad, ...] = ()
    uniform_loads: tuple[UniformLoad, ...] = ()
    deflection_limit: float = 360


@dataclass(frozen=True)
class BeamResults:
    x_ft: np.ndarray
    shear_kip: np.ndarray
    moment_kip_ft: np.ndarray
    deflection_in: np.ndarray
    reaction_left_kip: float
    reaction_right_kip: float
    fixed_moment_kip_ft: float
    max_moment_kip_ft: float
    max_deflection_in: float
    bending_stress_ksi: float
    allowable_deflection_in: float
    bending_pass: bool
    deflection_pass: bool


def validate_beam(beam: BeamInput) -> None:
    if beam.span_ft <= 0:
        raise ValueError("Span must be greater than zero.")
    if beam.deflection_limit <= 0:
        raise ValueError("Deflection limit must be greater than zero.")
    if beam.section.E_ksi <= 0 or beam.section.I_in4 <= 0 or beam.section.S_in3 <= 0:
        raise ValueError("Section E, I, and S values must be greater than zero.")
    if beam.section.allowable_stress_ksi <= 0:
        raise ValueError("Allowable stress must be greater than zero.")
    span = beam.span_ft
    for load in beam.point_loads:
        if not 0 <= load.position_ft <= span:
            raise ValueError("Point load positions must lie within the span.")
        if load.magnitude_kip < 0:
            raise ValueError("Load magnitudes must be non-negative.")
    for load in beam.uniform_loads:
        if not 0 <= load.start_ft < load.end_ft <= span:
            raise ValueError("Uniform load intervals must lie within the span.")
        if load.magnitude_kip_per_ft < 0:
            raise ValueError("Load magnitudes must be non-negative.")


def _uniform_resultant(load: UniformLoad) -> tuple[float, float]:
    magnitude = load.magnitude_kip_per_ft * (load.end_ft - load.start_ft)
    centroid = (load.start_ft + load.end_ft) / 2
    return magnitude, centroid


def _total_load_and_moment(beam: BeamInput) -> tuple[float, float]:
    total = sum(load.magnitude_kip for load in beam.point_loads)
    moment = sum(load.magnitude_kip * load.position_ft for load in beam.point_loads)
    for load in beam.uniform_loads:
        magnitude, centroid = _uniform_resultant(load)
        total += magnitude
        moment += magnitude * centroid
    return total, moment


def _reactions(beam: BeamInput) -> tuple[float, float, float]:
    total, load_moment = _total_load_and_moment(beam)
    if beam.support_type == "cantilever":
        return total, 0.0, -load_moment
    right = load_moment / beam.span_ft
    left = total - right
    return left, right, 0.0


def _positive_part(value: np.ndarray | float) -> np.ndarray | float:
    return np.maximum(value, 0)


def _moment_kip_ft(x_ft: np.ndarray, beam: BeamInput, left_reaction: float, fixed_moment: float) -> np.ndarray:
    moment = fixed_moment + left_reaction * x_ft
    for load in beam.point_loads:
        moment -= load.magnitude_kip * _positive_part(x_ft - load.position_ft)
    for load in beam.uniform_loads:
        start = _positive_part(x_ft - load.start_ft)
        end = _positive_part(x_ft - load.end_ft)
        moment -= load.magnitude_kip_per_ft * (start**2 - end**2) / 2
    return moment


def _shear_kip(x_ft: np.ndarray, beam: BeamInput, left_reaction: float) -> np.ndarray:
    shear = np.full_like(x_ft, left_reaction, dtype=float)
    for load in beam.point_loads:
        shear -= load.magnitude_kip * (x_ft >= load.position_ft)
    for load in beam.uniform_loads:
        loaded_length = np.clip(x_ft - load.start_ft, 0, load.end_ft - load.start_ft)
        shear -= load.magnitude_kip_per_ft * loaded_length
    return shear


def _deflection_in(x_in: np.ndarray, beam: BeamInput, left_reaction: float, fixed_moment: float) -> np.ndarray:
    """Integrate the piecewise moment expression twice in closed form."""
    E = beam.section.E_ksi
    I = beam.section.I_in4
    x_ft = x_in / 12
    numerator = fixed_moment * 12 * x_in**2 / 2
    numerator += left_reaction * x_in**3 / 6
    for load in beam.point_loads:
        distance = _positive_part(x_in - load.position_ft * 12)
        numerator -= load.magnitude_kip * distance**3 / 6
    for load in beam.uniform_loads:
        start = _positive_part(x_in - load.start_ft * 12)
        end = _positive_part(x_in - load.end_ft * 12)
        numerator -= load.magnitude_kip_per_ft / 12 * (start**4 - end**4) / 24
    if beam.support_type == "simply_supported":
        end_value = float(numerator[-1])
        numerator += (-end_value / (beam.span_ft * 12)) * x_in
    return numerator / (E * I)


def calculate_beam(beam: BeamInput, samples: int = 1001) -> BeamResults:
    validate_beam(beam)
    if samples < 2:
        raise ValueError("At least two calculation samples are required.")
    left, right, fixed_moment = _reactions(beam)
    x_ft = np.linspace(0, beam.span_ft, samples)
    shear = _shear_kip(x_ft, beam, left)
    moment = _moment_kip_ft(x_ft, beam, left, fixed_moment)
    deflection = _deflection_in(x_ft * 12, beam, left, fixed_moment)
    max_moment = float(np.max(np.abs(moment)))
    max_deflection = float(np.max(np.abs(deflection)))
    bending_stress = max_moment * 12 / beam.section.S_in3
    allowable_deflection = beam.span_ft * 12 / beam.deflection_limit
    return BeamResults(
        x_ft=x_ft,
        shear_kip=shear,
        moment_kip_ft=moment,
        deflection_in=deflection,
        reaction_left_kip=left,
        reaction_right_kip=right,
        fixed_moment_kip_ft=fixed_moment,
        max_moment_kip_ft=max_moment,
        max_deflection_in=max_deflection,
        bending_stress_ksi=bending_stress,
        allowable_deflection_in=allowable_deflection,
        bending_pass=bending_stress <= beam.section.allowable_stress_ksi,
        deflection_pass=max_deflection <= allowable_deflection,
    )
