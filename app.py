"""Tkinter entry point for the Beam Designer."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import json

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages

from beam_calculations import BeamInput, PointLoad, UniformLoad, calculate_beam
from plotting import make_figure
from section_properties import SECTIONS


class LoadRow(ttk.Frame):
    def __init__(self, parent: tk.Misc, load_type: str, remove_callback) -> None:
        super().__init__(parent)
        self.load_type = tk.StringVar(value=load_type)
        self.magnitude = tk.StringVar()
        self.start = tk.StringVar()
        self.end = tk.StringVar()
        ttk.Combobox(self, textvariable=self.load_type, values=("Point", "Uniform"), width=9, state="readonly").grid(row=0, column=0, padx=2)
        ttk.Entry(self, textvariable=self.magnitude, width=9).grid(row=0, column=1, padx=2)
        ttk.Entry(self, textvariable=self.start, width=9).grid(row=0, column=2, padx=2)
        ttk.Entry(self, textvariable=self.end, width=9).grid(row=0, column=3, padx=2)
        ttk.Button(self, text="Remove", command=remove_callback).grid(row=0, column=4, padx=2)


class BeamDesigner(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Beam Designer")
        self.minsize(1000, 650)
        self.load_rows: list[LoadRow] = []
        self.figure_canvas: FigureCanvasTkAgg | None = None
        self._build_controls()
        self._add_example_loads()
        self._calculate()

    def _build_controls(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        controls = ttk.Frame(self, padding=12)
        controls.grid(row=0, column=0, sticky="ns")
        output = ttk.Frame(self, padding=8)
        output.grid(row=0, column=1, sticky="nsew")
        output.columnconfigure(0, weight=1)
        output.rowconfigure(1, weight=1)

        self.support = tk.StringVar(value="Simply supported")
        self.span = tk.StringVar(value="20")
        self.section = tk.StringVar(value="W12x26")
        self.deflection_limit = tk.StringVar(value="360")
        self._build_menu()
        ttk.Label(controls, text="Beam inputs", font=("TkDefaultFont", 12, "bold")).grid(column=0, columnspan=2, sticky="w")
        ttk.Label(controls, text="Support").grid(row=1, column=0, sticky="w", pady=(12, 2))
        ttk.Combobox(controls, textvariable=self.support, values=("Simply supported", "Cantilever"), state="readonly", width=18).grid(row=1, column=1)
        ttk.Label(controls, text="Span (ft)").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(controls, textvariable=self.span, width=20).grid(row=2, column=1)
        ttk.Label(controls, text="Section").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Combobox(controls, textvariable=self.section, values=tuple(SECTIONS), state="readonly", width=18).grid(row=3, column=1)
        ttk.Label(controls, text="Deflection limit (L/)").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(controls, textvariable=self.deflection_limit, width=20).grid(row=4, column=1)

        load_frame = ttk.LabelFrame(controls, text="Loads (downward)")
        load_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=12)
        for column, heading in enumerate(("Type", "Magnitude", "Start (ft)", "End (ft)", "")):
            ttk.Label(load_frame, text=heading).grid(row=0, column=column, padx=2)
        self.rows_frame = ttk.Frame(load_frame)
        self.rows_frame.grid(row=1, column=0, columnspan=5)
        ttk.Button(load_frame, text="Add load", command=lambda: self._add_load_row("Point")).grid(row=2, column=0, columnspan=5, pady=5)
        ttk.Button(controls, text="Calculate", command=self._calculate).grid(row=6, column=0, columnspan=2, sticky="ew")
        self.summary = tk.StringVar()
        ttk.Button(controls, text="Export results CSV", command=self._export_csv).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Button(controls, text="Calculation sheet PDF", command=self._export_pdf).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Label(controls, textvariable=self.summary, justify="left", wraplength=250).grid(row=9, column=0, columnspan=2, sticky="nw", pady=12)

        self.status = tk.StringVar(value="Ready")
        ttk.Label(output, text="Beam diagrams", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(output, textvariable=self.status).grid(row=2, column=0, sticky="w")

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Save", command=self._save)
        file_menu.add_command(label="Open", command=self._open)
        menu.add_cascade(label="File", menu=file_menu)
        self.config(menu=menu)

    def _add_load_row(self, load_type: str, values: tuple[str, str, str] | None = None) -> None:
        row = LoadRow(self.rows_frame, load_type, lambda: self._remove_load_row(row))
        row.pack(fill="x", pady=2)
        if values:
            row.magnitude.set(values[0])
            row.start.set(values[1])
            row.end.set(values[2])
        self.load_rows.append(row)

    def _remove_load_row(self, row: LoadRow) -> None:
        row.destroy()
        self.load_rows.remove(row)

    def _add_example_loads(self) -> None:
        self._add_load_row("Uniform", ("1", "0", "20"))

    def _read_beam(self) -> BeamInput:
        span = float(self.span.get())
        point_loads = []
        uniform_loads = []
        for row in self.load_rows:
            magnitude = float(row.magnitude.get())
            start = float(row.start.get())
            end = float(row.end.get()) if row.end.get().strip() else start
            if row.load_type.get() == "Point":
                point_loads.append(PointLoad(start, magnitude))
            else:
                uniform_loads.append(UniformLoad(start, end, magnitude))
        support = "cantilever" if self.support.get() == "Cantilever" else "simply_supported"
        return BeamInput(
            span, support, SECTIONS[self.section.get()], tuple(point_loads), tuple(uniform_loads),
            float(self.deflection_limit.get()),
        )

    def _design_data(self) -> dict:
        beam = self._read_beam()
        return {
            "support_type": beam.support_type,
            "span_ft": beam.span_ft,
            "section": beam.section.name,
            "deflection_limit": beam.deflection_limit,
            "point_loads": [{"position_ft": load.position_ft, "magnitude_kip": load.magnitude_kip} for load in beam.point_loads],
            "uniform_loads": [{"start_ft": load.start_ft, "end_ft": load.end_ft, "magnitude_kip_per_ft": load.magnitude_kip_per_ft} for load in beam.uniform_loads],
        }

    def _save(self) -> None:
        try:
            data = self._design_data()
        except (KeyError, ValueError) as error:
            messagebox.showerror("Cannot save design", str(error))
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=(("Beam design", "*.json"), ("All files", "*.*")))
        if path:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

    def _open(self) -> None:
        path = filedialog.askopenfilename(filetypes=(("Beam design", "*.json"), ("All files", "*.*")))
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
            self.support.set("Cantilever" if data["support_type"] == "cantilever" else "Simply supported")
            self.span.set(str(data["span_ft"]))
            self.section.set(data["section"])
            self.deflection_limit.set(str(data["deflection_limit"]))
            for row in self.load_rows:
                row.destroy()
            self.load_rows.clear()
            for load in data["point_loads"]:
                self._add_load_row("Point", (str(load["magnitude_kip"]), str(load["position_ft"]), ""))
            for load in data["uniform_loads"]:
                self._add_load_row("Uniform", (str(load["magnitude_kip_per_ft"]), str(load["start_ft"]), str(load["end_ft"])))
            self._calculate()
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            messagebox.showerror("Cannot open design", str(error))

    def _calculated(self):
        beam = self._read_beam()
        return beam, calculate_beam(beam)

    def _export_csv(self) -> None:
        try:
            _, results = self._calculated()
        except (KeyError, ValueError) as error:
            messagebox.showerror("Cannot export results", str(error))
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if path:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(("x (ft)", "V (kip)", "M (kip-ft)", "Deflection (in)"))
                writer.writerows(zip(results.x_ft, results.shear_kip, results.moment_kip_ft, results.deflection_in))

    def _export_pdf(self) -> None:
        try:
            beam, results = self._calculated()
        except (KeyError, ValueError) as error:
            messagebox.showerror("Cannot export PDF", str(error))
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")))
        if path:
            figure = make_figure(beam, results)
            figure.suptitle(
                f"Beam Designer | {beam.section.name} | {beam.span_ft:g} ft | "
                f"{beam.support_type.replace('_', ' ').title()}\n"
                f"Deflection limit L/{beam.deflection_limit:g} | "
                f"Bending {'PASS' if results.bending_pass else 'FAIL'} | "
                f"Deflection {'PASS' if results.deflection_pass else 'FAIL'}",
                fontsize=10,
            )
            with PdfPages(path) as pdf:
                pdf.savefig(figure)
            figure.clear()

    def _calculate(self) -> None:
        try:
            beam = self._read_beam()
            results = calculate_beam(beam)
        except (KeyError, ValueError) as error:
            self.status.set("Input error")
            messagebox.showerror("Cannot calculate beam", str(error))
            return
        if self.figure_canvas:
            self.figure_canvas.get_tk_widget().destroy()
            self.figure_canvas.figure.clear()
        self.figure_canvas = FigureCanvasTkAgg(make_figure(beam, results), master=self.grid_slaves(row=0, column=1)[0])
        self.figure_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
        self.figure_canvas.draw()
        reaction = f"Reactions: {results.reaction_left_kip:.2f} k"
        if beam.support_type == "simply_supported":
            reaction += f", {results.reaction_right_kip:.2f} k"
        self.summary.set(
            f"{reaction}\n"
            f"Max moment: {results.max_moment_kip_ft:.2f} kip-ft\n"
            f"Max deflection: {results.max_deflection_in:.3f} in "
            f"(limit {results.allowable_deflection_in:.3f})\n"
            f"Bending: {'PASS' if results.bending_pass else 'FAIL'}\n"
            f"Deflection: {'PASS' if results.deflection_pass else 'FAIL'}"
        )
        self.status.set("Calculated")


if __name__ == "__main__":
    BeamDesigner().mainloop()
