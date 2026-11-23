"""Matplotlib views for beam results."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from beam_calculations import BeamInput, BeamResults


def make_figure(beam: BeamInput, results: BeamResults) -> Figure:
    figure, axes = plt.subplots(4, 1, figsize=(8, 8), constrained_layout=True)
    x = results.x_ft
    axes[0].plot(x, [0] * len(x), color="black", linewidth=3)
    for load in beam.point_loads:
        axes[0].annotate("↓", (load.position_ft, 0), xytext=(0, 12), textcoords="offset points", ha="center")
    for load in beam.uniform_loads:
        axes[0].plot([load.start_ft, load.end_ft], [0, 0], color="tab:red", linewidth=6, alpha=0.5)
    axes[0].set_title("Beam and loads")
    axes[0].set_ylabel("Beam")
    axes[1].plot(x, results.shear_kip, color="tab:blue")
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_ylabel("V (kip)")
    axes[1].set_title("Shear")
    axes[2].plot(x, results.moment_kip_ft, color="tab:green")
    axes[2].axhline(0, color="black", linewidth=0.8)
    axes[2].set_ylabel("M (kip-ft)")
    axes[2].set_title("Moment")
    axes[3].plot(x, results.deflection_in, color="tab:purple")
    axes[3].axhline(0, color="black", linewidth=0.8)
    axes[3].set_ylabel("Deflection (in)")
    axes[3].set_xlabel("Position (ft)")
    axes[3].set_title("Deflection")
    return figure
