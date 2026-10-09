# Instrumentation and System Design for Advanced MRI Imaging

A low-field, benchtop MRI system built from two **Digilent Analog Discovery 2 (AD2)** devices and controlled entirely in Python. The project generates a spin-echo pulse sequence with frequency- and phase-encoding gradients, acquires 32 phase-encoded echoes, and reconstructs a 2D image of a phantom with a 2D Fourier transform.

**Authors:** Austin Janszen, Jen Li Kao

<p align="center">
  <img src="images/k_space.png" width="30%" alt="Phase-encoded k-space">
  <img src="images/reconstructed_image.png" width="30%" alt="Reconstructed image">
  <img src="images/filtered_image.png" width="30%" alt="Reconstructed image with threshold filter">
  <br>
  <em>Left to right: phase-encoded k-space, reconstructed image, and reconstructed image after thresholding.</em>
</p>

---

## Contents

| File | Description |
| --- | --- |
| [`Phase_Encode_Image.py`](Phase_Encode_Image.py) | Acquisition script: parameter GUI, AD2 setup, RF / gradient / timing control, and data capture for every phase-encode step. |
| [`Phase_Encode_reconstruction.py`](Phase_Encode_reconstruction.py) | Offline reconstruction: builds k-space from the saved spectra and reconstructs the image with a 2D FFT. |
| [`Final_Image_Result.pdf`](Final_Image_Result.pdf) | Slides summarizing the results and findings. |
| [`images/`](images) | Result figures used in this README. |

## How it works

### 1. Pulse sequence (AD2 #1)

- **RF excitation:** waveform generator W1 outputs a sine burst at the Larmor frequency (default 3.34 MHz), `Npulse` pulses of width `Tp`, separated by `predelay = TE/2 − Tp`, forming a spin echo.
- **Local oscillator:** waveform generator W2 outputs `f₀ − 200 kHz`, mixing the echo down to a 200 kHz intermediate frequency (IF).
- **Digitizer:** oscilloscope channel 1 records the echo for `Tacq` at `sampFreq` (default 1 MS/s).
- **Timing (digital I/O, 10 µs resolution):**

  | DIO pin | Function |
  | --- | --- |
  | 0 | External oscilloscope trigger |
  | 2 | T/R switch |
  | 3 | Attenuator |
  | 4 | AD2 digitizer trigger |

- **Power supply:** +5 V rail enabled for the front-end electronics.

### 2. Gradients and shims (AD2 #2)

- **W1 – frequency encoding:** dephase lobe followed by a readout lobe centered on the echo, with linear ramps of `T_ramp`.
- **W2 – phase encoding:** a trapezoidal lobe whose amplitude steps through 32 values from −G<sub>max</sub> to +G<sub>max</sub>.
- **Shims:** optional DC offsets on the same outputs (limited to ±0.2 V).

The gradient strength needed for the requested resolution is computed in the GUI as

```
G  = (1 / Tacq) / resolution / 425.7 × (1.28 / 0.56)   [G/cm, with calibration factor]
V_coil = 4 × G / 0.5                                    [V into the gradient coils]
V_AD2  = V_coil / 11                                    [V from the AD2, amplifier gain 11]
```

### 3. Signal processing (per phase-encode step)

1. Acquire the echo (repeated `Num Averages` times).
2. 6th-order Chebyshev type II band-pass filter, IF ± 40 kHz, 40 dB stop-band (`filtfilt`, zero phase).
3. Hamming window, then FFT.
4. Average the spectra and save them to `phase_encode_data_<n>_v1.txt`.

### 4. Image reconstruction

1. Load the 32 spectra and keep 64 points around the 200 kHz IF.
2. Inverse FFT each one to get a line of k-space (32 × 64 matrix).
3. Apply a 2D Hamming window to suppress ringing.
4. 2D FFT, take the magnitude, and center the image.
5. Zero all pixels below 20 % of the maximum to remove background noise.

## Getting started

### Hardware

- 2 × Digilent Analog Discovery 2
  - AD2 #1: RF transmit, LO, digitizer, DIO timing, +5 V supply
  - AD2 #2: gradient waveforms (and shims), triggered externally by AD2 #1
- Permanent magnet, RF coil, T/R switch, attenuator, mixer, and gradient coils with an amplifier (gain ≈ 11)

### Software

- Python 3
- [Digilent WaveForms](https://digilent.com/reference/software/waveforms/waveforms-3/start) (installs the `dwf` runtime library)
- `dwfconstants.py` from the WaveForms SDK samples (`.../WaveForms/samples/py/`), placed next to the scripts
- Python packages:

  ```bash
  pip install numpy scipy matplotlib
  ```

  `tkinter` ships with most Python installations.

### 1. Acquire data

```bash
python Phase_Encode_Image.py
```

A parameter window opens:

| Parameter | Default | Meaning |
| --- | --- | --- |
| Frequency (MHz) | 3.34 | Larmor / RF frequency |
| Amplitude (V) | 1 | RF amplitude |
| TE (ms) | 10 | Echo time |
| Tp (µs) | 25 | RF pulse width |
| Npulse | 2 | Number of RF pulses |
| sampFreq | 1 000 000 | Digitizer sample rate (Hz) |
| Tacq (ms) | 8.192 | Acquisition window |
| Resolution (mm) | 333 | Target resolution (sets gradient strength) |
| T_ramp (ms) | 5 | Gradient ramp time |
| Num Averages | 1 | Averages per phase-encode step |
| Filtering / Window / Gradient / Shim | on | Enable each processing or hardware stage |

The window shows the derived predelay, sample count, gradient strength, and required voltages as you type. Parameter sets can be saved and loaded as CSV files; the last run is stored in `Recent.csv`. Press **Run** to start the 32-step scan. One `phase_encode_data_<n>_v1.txt` file is written per step.

### 2. Reconstruct the image

Set `directory` in `Phase_Encode_reconstruction.py` to the folder containing the `phase_encode_data_*_v1.txt` files, then run:

```bash
python Phase_Encode_reconstruction.py
```

This displays the k-space magnitude and the reconstructed image.

## Results and findings

- Phase encoding produced a clean k-space acquisition, and the 2D Hamming window reduced reconstruction artifacts.
- The reconstructed image matched the phantom geometry.
- Results stayed consistent across different resolutions and numbers of projections.
- Artifacts remained on one phantom, likely caused by environmental factors such as temperature drift or electromagnetic interference.

See [`Final_Image_Result.pdf`](Final_Image_Result.pdf) for details.

## License

Released under the [MIT License](LICENSE).
