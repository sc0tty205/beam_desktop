import pytest

from beam_calculations import BeamInput, PointLoad, UniformLoad, calculate_beam
from section_properties import SECTIONS


def test_full_span_uniform_load_validation_case() -> None:
    beam = BeamInput(
        span_ft=20,
        support_type="simply_supported",
        section=SECTIONS["W12x26"],
        uniform_loads=(UniformLoad(0, 20, 1),),
    )
    result = calculate_beam(beam)
    assert result.max_moment_kip_ft == pytest.approx(50, abs=0.05)
    assert result.max_deflection_in == pytest.approx(0.609, abs=0.002)


def test_partial_uniform_load_validation_case() -> None:
    beam = BeamInput(
        span_ft=30,
        support_type="simply_supported",
        section=SECTIONS["W18x35"],
        uniform_loads=(UniformLoad(0, 15, 2),),
    )
    result = calculate_beam(beam)
    assert result.reaction_left_kip == pytest.approx(22.5)
    assert result.reaction_right_kip == pytest.approx(7.5)
    assert result.max_moment_kip_ft == pytest.approx(126.6, abs=0.2)


def test_cantilever_point_load_has_fixed_reactions() -> None:
    beam = BeamInput(
        span_ft=10,
        support_type="cantilever",
        section=SECTIONS["W12x26"],
        point_loads=(PointLoad(10, 1),),
    )
    result = calculate_beam(beam)
    assert result.reaction_left_kip == pytest.approx(1)
    assert result.fixed_moment_kip_ft == pytest.approx(-10)
    assert result.moment_kip_ft[-1] == pytest.approx(0)
