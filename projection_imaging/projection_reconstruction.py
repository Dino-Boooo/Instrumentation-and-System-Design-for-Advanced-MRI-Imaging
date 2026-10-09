"""Projection reconstruction (backprojection).

Select the projection .txt files in the file dialog. Each projection is
shifted back to a common center (shift_amounts, tuned for our 32-angle data),
values below 30 % of its peak are zeroed, and the projections are stacked into
a sinogram and reconstructed with skimage.transform.iradon, both as a plain
and as a Hamming-filtered backprojection.
"""

import numpy as np
import matplotlib.pyplot as plt
from skimage.transform import iradon
from tkinter import Tk, filedialog
from math import ceil, sqrt, floor

# Function to shift data
def shift_data(data, shift_amount):
    return np.roll(data, shift_amount)

# 1. Open a file dialog
def select_files():
    root = Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(
        title='Select projection files',
        filetypes=[('Text Files', '*.txt')]
    )
    return list(file_paths)

# 2. Prompt user to select projection files 
txt_files = select_files()

if not txt_files:
    print("No files selected. Exiting...")
    exit()

# 3. Load files with shift amounts for each file
#shift_amounts = [0, -2, -1, 5]  # Define specific shift amounts for each file
shift_amounts = [0, 0, 0, 0, 0, 1, 1, 1, 1, 10, 10, 10, 10 ,10 ,10, 15, 15, 16, 18, 18, 20, 20, 22, 23, 23, 25, 25, 28, 28, 28, 28, 28]
for i in range(0, len(shift_amounts)):
    shift_amounts[i]+= 25
 
projections = []
for i, f in enumerate(txt_files):
    data = np.loadtxt(f, skiprows=1)
    shifted_data = shift_data(data[:, 1], shift_amounts[i % len(shift_amounts)])  # Apply shift
    projections.append(shifted_data)
                       
print(f"Loaded and shifted {len(projections)} files:")
for f in txt_files:
    print(f" - {f}")

# angles
Npe = len(projections)
theta_array = np.linspace(0, 180, Npe + 1)[:-1]

cols = floor(sqrt(Npe))  # Set columns based on square root of Npe
rows = ceil(Npe / cols)  # Adjust rows accordingly

# Plot the projections
fig, axes = plt.subplots(rows, cols, figsize=(10, 10))
axes = axes.ravel()

for i, (proj, angle) in enumerate(zip(projections, theta_array)):
    proj[proj <= 0.3 * np.max(proj)] = 0
    axes[i].plot(proj)
    axes[i].set_title(f'{angle} degrees')

plt.tight_layout()
plt.show()

# Concatenate projections to form the Radon Transform matrix
R = np.column_stack(projections)

# Take the inverse Radon Transform with no filtering (Straight Backprojection Summation)
I = iradon(R, theta=theta_array, filter_name=None)

# Plot the Radon Transform and the reconstructed image
plt.figure()
plt.imshow(R.T, cmap='gray', aspect='auto')
plt.title('Radon Transform')
plt.colorbar()
plt.show()

plt.figure()
plt.imshow(I, cmap='gray')
plt.title('Straight Backprojection Summation Reconstruction')
plt.colorbar()
plt.show()

# Using Filtered Backprojection with Hamming filter
reconstruction_fbp = iradon(R, theta=theta_array, filter_name='hamming')
plt.figure()
plt.imshow(np.abs(reconstruction_fbp), cmap='gray')
plt.title('Reconstructed Image using Hamming Filter')
plt.colorbar()
plt.show()
