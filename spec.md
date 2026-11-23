# Beam Designer

## Platform
- Python desktop app using Tkinter, started with `python app.py`
- Calculations with numpy, kept in their own module, separate from
  the window code
- Diagrams drawn with matplotlib, embedded in the window

## Purpose
Shear, moment, and deflection diagrams for a beam, with a check of
whether the beam is strong and stiff enough.

## Inputs
- Simply supported or cantilever, and the span (ft)
- Point loads and uniform loads
- A steel W-shape or a lumber size

## Calculations
- Reactions, shear, and moment from statics
- Deflection
- Bending stress fb = M/S, compared to the allowable stress
- Deflection compared to L/360

## Outputs
- The beam with its loads, and the three diagrams
- Pass or fail for bending and deflection

## Look and feel
- Clean and professional, with an example beam loaded when it opens.
- inputs in a panel on the left, the beam and diagrams on the right, and a window that can be resized.
- Remove the lines about phones.

## Validation
- 20 ft simply supported W12x26 with 1 kip/ft: M = 50.0 kip-ft,
deflection 0.609 in.
- Simply supported, 30 ft, W18x35, uniform 2 kips/ft from 0 to 15 ft
   only: reactions 22.5 k (left) and 7.5 k (right); max moment
   126.6 kip-ft at 11.25 ft.

## Out of scope
Continuous beams and buckling.

## Desktop Features
- Save and Open: A File menu with a button called "Save" that saves the beam (support type, span, section, deflection limit, and loads) to a file and and a button called "Open" that opens it again. Remove "Saving designs" from the Out of scope section of the spec first.
- Export results: A button that saves a table of x, V, M, and deflection along the beam to a CSV file that opens in Excel.
- Calculation sheet: A button that saves the diagrams and checks as a PDF, with the inputs listed at the top, ready to hand in with a design.