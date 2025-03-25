import numpy as np
import matplotlib.pyplot as plt
import os



fov = 30000
Npe = 32
sampFreq = 1e6
freq = 200e3


# Define the directory containing the files
directory = r'\\coe-fs.engr.tamu.edu\Ugrads\hottroddaj\Downloads\phase_encode_data_v8'

# Initialize k-space data
k_space_data = np.zeros((Npe, 64), dtype=complex)
for i in range(Npe):
    filename = os.path.join(directory, f'phase_encode_data_{i}_v1.txt')
    
    fft_data = np.loadtxt(filename, skiprows=1, dtype=complex)
    
    
    fft_freqs = np.fft.fftfreq(len(fft_data), 1/sampFreq)
    
    center_index = np.argmin(abs(fft_freqs - freq))
    # Window FFt

    fft_windowed = fft_data[center_index - 32 :center_index + 32]
    # Take IFFT 
    ifft_windowed = np.fft.ifft(fft_windowed)
    # Read into Kspace
    k_space_data[i, :] = ifft_windowed
    
    
window = np.hamming(Npe)
window2 = np.hamming(64)
window_2d = np.outer(window, window2)
k_space_data *= window_2d


# 2D FFT of k-space
reconstructed_image = np.fft.fft2(k_space_data)

# take magnitude
magnitude_image = np.abs(reconstructed_image)
magnitude_image = np.roll(magnitude_image, 50)
magnitude_image = np.roll(magnitude_image.T, 13)
magnitude_image = magnitude_image.T

magnitude_image[magnitude_image <= 0.2 * np.max(magnitude_image)] = 0


# Display the k-space (magnitude of complex values)
plt.imshow(np.abs(k_space_data), cmap='jet', extent=[-fov/2, fov/2, -fov/2, fov/2])
plt.title("k-space")
plt.show()

# Display the reconstructed image
plt.imshow(magnitude_image, cmap='gray', extent=[-fov/2, fov/2, -fov/2, fov/2])
plt.title("Phase Encoded Image")
plt.show()