"""Built-in section properties for the initial beam designer."""

from beam_calculations import SectionProperties

SECTIONS = {
    "W12x26": SectionProperties(
        name="W12x26",
        E_ksi=29000,
        I_in4=204,
        S_in3=33.9,
        allowable_stress_ksi=24,
    ),
    "W18x35": SectionProperties(
        name="W18x35",
        E_ksi=29000,
        I_in4=510,
        S_in3=57.6,
        allowable_stress_ksi=24,
    ),
    "2x10 lumber": SectionProperties(
        name="2x10 lumber",
        E_ksi=1600,
        I_in4=84.6,
        S_in3=16.9,
        allowable_stress_ksi=1.15,
    ),
}
