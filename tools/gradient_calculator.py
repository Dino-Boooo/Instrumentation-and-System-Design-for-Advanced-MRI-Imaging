"""Standalone gradient-strength calculator.

Early prototype of the parameter GUI: computes the gradient strength in G/cm
needed for a target resolution and acquisition time,
G = (1 / Tacq) / resolution / 425.7.
"""

import tkinter as tk
from tkinter import ttk

# Define the function to calculate the gradient strength
def calculate_gradient():
    try:
        # Get input data from the GUI
        TE = float(te_entry.get())   # Echo Time in seconds
        TR = float(tr_entry.get())  # Repetition Time in seconds
        T_acq = float(tacq_entry.get())   # Acquisition Time in seconds
        Resolution = float(res_entry.get())   # Resolution in meters (converted from microns)
        FOV = float(fov_entry.get())   # Field of View in meters
        Conversion_factor = 425.7  # Hz -> G/cm conversion factor
        
        # Calculate frequency per point
        Freq_per_point = 1 / T_acq
        
        # Calculate the gradient strength G
        G = Freq_per_point / Resolution
        
        # Convert Hz/mm to G/cm
        G_cm = G / Conversion_factor

        # Update the result display
        result_label.config(text=f"Computed Gradient Strength: {G_cm:.3f} G/cm")

    except ValueError:
        result_label.config(text="Please enter valid numbers!")

# Create the main window
root = tk.Tk()
root.title("Gradient Strength Calculator")

# Create input fields and labels
ttk.Label(root, text="TE (s)").grid(row=0, column=0, padx=10, pady=10)
te_entry = ttk.Entry(root)
te_entry.grid(row=0, column=1, padx=10, pady=10)

ttk.Label(root, text="TR (s)").grid(row=1, column=0, padx=10, pady=10)
tr_entry = ttk.Entry(root)
tr_entry.grid(row=1, column=1, padx=10, pady=10)

ttk.Label(root, text="T_acq (s)").grid(row=2, column=0, padx=10, pady=10)
tacq_entry = ttk.Entry(root)
tacq_entry.grid(row=2, column=1, padx=10, pady=10)

ttk.Label(root, text="Resolution (mm)").grid(row=3, column=0, padx=10, pady=10)
res_entry = ttk.Entry(root)
res_entry.grid(row=3, column=1, padx=10, pady=10)

ttk.Label(root, text="FOV (cm)").grid(row=4, column=0, padx=10, pady=10)
fov_entry = ttk.Entry(root)
fov_entry.grid(row=4, column=1, padx=10, pady=10)

# Create the calculate button
calculate_button = ttk.Button(root, text="Calculate Gradient", command=calculate_gradient)
calculate_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Display the result label
result_label = ttk.Label(root, text="")
result_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

# Start the GUI event loop
root.mainloop()
