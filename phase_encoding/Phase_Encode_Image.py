from dwfconstants import *
import tkinter as tk
from tkinter import filedialog
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import time
import csv
from scipy.signal import cheby2, filtfilt
from scipy.fftpack import fft, fftfreq
from scipy.signal import find_peaks
from datetime import datetime
##   Hide the SDK functions by left click next to the if statement
import_mre_functions = 1

if import_mre_functions == 1:
    
  
    def set_dio(ChNum,totalCycles,low,high):
        #   The DIO can be set by the number of cycles low, then high, and then low again. 
        #   Input values are in seconds, then converted to cycles assuming 1 clock cycle/ 10 microseconds.  
        DIOLow1 = int(low * 10**5)
        DIOHigh = int(high * 10**5)
        DIOLow2 = int(totalCycles - DIOHigh - DIOLow1)
        dwf.FDwfDigitalOutEnableSet(hdwf, c_int(ChNum), c_int(1))
        dwf.FDwfDigitalOutDividerSet(hdwf, c_int(ChNum), c_int(int(hzSys.value / 100000)))
        dwf.FDwfDigitalOutCounterSet(hdwf, c_int(ChNum), c_int(DIOLow2), c_int(DIOHigh))
        dwf.FDwfDigitalOutCounterInitSet(hdwf, c_int(ChNum), c_int(0), c_int(DIOLow1))
        dwf.FDwfDigitalOutIdleSet(hdwf, c_int(ChNum), DwfDigitalOutIdleLow)
        return 
    
    def set_scope(sampFreq,numSamp,acqTime,Delay):
        dwf.FDwfAnalogInAcquisitionModeSet(hdwf, acqmodeSingle)  # set to a single acquisition
        dwf.FDwfAnalogInFrequencySet(hdwf, c_double(sampFreq))  # sets up the frequency
        dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(numSamp))  # sets the buffer
        dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))  # enables channel 0
        dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_bool(False))  # disable  channel 1
        dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(-1), c_double(5))  # sets the range
        dwf.FDwfAnalogInChannelFilterSet(hdwf, c_int(-1), filterDecimate)  
        dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcExternal1)  # sets the trigger source
        dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeRise)
        dwf.FDwfAnalogInTriggerPositionSet(hdwf, c_double(acqTime / 2 + Delay) ) # sets the trigger position
        y = 0
        return y
    
    def set_wavegen(ChNum,freq,amplitude,pulseL,pd,Nreps):
        dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(ChNum), AnalogOutNodeCarrier, c_bool(True))
        dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(ChNum), AnalogOutNodeCarrier, funcSine)  # Function
        dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(ChNum), AnalogOutNodeCarrier, c_double(freq))  # frequency
        dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(ChNum), AnalogOutNodeCarrier, c_double(amplitude))  # Amplitude
        dwf.FDwfAnalogOutRunSet(hdwf, c_int(ChNum), c_double(pulseL))  # run time
        dwf.FDwfAnalogOutWaitSet(hdwf, c_int(ChNum), c_double(pd))  # wait time
        dwf.FDwfAnalogOutRepeatSet(hdwf, c_int(ChNum), c_int(Nreps))  # repetitions
#        dwf.FDwfAnalogOutTriggerSourceSet(hdwf, c_int(ChNum), trigsrcExternal1)  # sets the trigger source        
        dwf.FDwfAnalogOutTriggerSourceSet(hdwf, c_int(ChNum), trigsrcDigitalOut)  # sets the trigger source
        y = 0
        return y   

    def set_pos_powersupply(Voltage):
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(0), c_double(True))  # enable positive supply
        dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(1), c_double(Voltage))  # set voltage to 5 V
        dwf.FDwfAnalogIOEnableSet(hdwf, c_int(True))  # master enable
        y = 0
        return y
 
    def arm_dio(totalTime):
        # Finishing setting up the DIO pins.
        dwf.FDwfDigitalOutRunSet(hdwf, c_double(totalTime))
        dwf.FDwfDigitalOutWaitSet(hdwf, c_double(0))
        dwf.FDwfDigitalOutRepeatSet(hdwf, c_int(1))
        y = 0
        return y
    
    def trigger_and_read_ch0(rgdSamples,numSamp):
        dwf.FDwfDigitalOutConfigure(hdwf, c_int(1))
        while True:
            dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
            if sts.value == DwfStateDone.value:
                break
        dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples, numSamp)  # get channel 1 data
        # dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSampless, 8192) # get channel 2 data
        y = 0
        return y
    
    def arm_analog():
        dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))
        dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_bool(True))
        dwf.FDwfAnalogOutConfigure(hdwf, c_int(1), c_bool(True))
        y = 0
        return y
    
    def set_ad2_device(idevice):
        dwf.FDwfEnumDeviceName(c_int(idevice), devicename)
        dwf.FDwfEnumSN(c_int(idevice), serialnum)
        hdwf.value = rghdwf[idevice]
        y = 0
        return y
    
    def reset_and_close():
        dwf.FDwfDigitalIOReset()
        dwf.FDwfDeviceCloseAll()
        y = 0
        return y

###################################################################
       # GUI
##################################################################

# Global variable to store RF parameters
RF_params = {}


# Function to save RF_params to a CSV file
def save_params_to_csv(filename):
    with open(f"{filename}.csv", "w", newline='') as f:
        writer = csv.writer(f)
        # Write the header
        writer.writerow(["Parameter", "Value"])
        # Write the data
        for key, value in RF_params.items():
            writer.writerow([key, value])

# Function to load RF_params from a CSV file
def load_params_from_csv(filename):
    global RF_params
    RF_params = {}  # Reset to empty
    try:
        with open(f"{filename}.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header
            for row in reader:
                if row:
                    key, value = row
                    # Convert value to appropriate type
                    if key in ["Frequency", "Amplitude", "TE", "Tp", "Tacq", "Resolution", "T_ramp"]:
                        RF_params[key] = float(value)
                    elif key in ["Npulse", "sampFreq", "Num_averages"]:
                        RF_params[key] = int(value)
                    else:
                        RF_params[key] = value.lower() == 'true'  # Convert to boolean
    except FileNotFoundError:
        RF_params = {}  # Reset to empty if file not found
    except Exception as e:
        print(f"Error loading parameters: {e}")
        RF_params = {}  # Reset to empty if there's any error
        
        
# Function to calculate and display values
def update_values(*args):
    global freq, amplitude, TE, Tp, Npulse, sampFreq, Tacq, filtering, window, gradient, shim, predelay, numSamp, resolution, T_ramp, num_averages, G_strength, echo_filename, V_AD2  # Declare global variables
    try:
        # Get input values and convert to float
        freq = float(frequency_var.get()) * 1e6
        amplitude = float(amplitude_var.get())
        TE = float(te_var.get()) *1e-3
        Tp = float(tp_var.get()) *1e-6
        Npulse = int(Npulse_var.get())       
        sampFreq = int(sampFreq_var.get()) 
        Tacq = float(Tacq_var.get()) *1e-3
        resolution = float(resolution_var.get()) *1e-3
        T_ramp= float(T_ramp_var.get()) * 1e-3
        num_averages= int(num_averages_var.get())
        filtering = filtering_var.get()
        window = window_var.get()
        gradient = gradient_var.get()
        shim = shim_var.get()
        echo_filename = echo_filename_var.get()
        
        # Calculate predelay
        predelay = (TE / 2) - Tp
        
        # Calculate number of Samples
        numSamp = int(Tacq * sampFreq)
        
        # Calculate gradiant strength
        
        G_strength = ((1/Tacq) / (resolution)) / 425.7
        
        Gradient_calibration = 1.28/0.56
        
        G_strength = G_strength * Gradient_calibration
        
        #Required Voltage into Gradiant Coils
        V_grad = 4 * (G_strength / 0.5)
        
        #Required Voltage from AD2
        
        V_AD2 = V_grad / 11
        
        
        # Display the values and predelay
        result_label.config(text=(
            f"Predelay: {predelay*1e3:.2f} ms \n"
            f"NumSamples: {numSamp} \n"
            f"Gradiant Srength: {G_strength:.2f} G/cm \n"
            f"Gradiant Coil Voltage Required: {V_grad:.2f} V \n"
            f"Voltage Required from AD2: {V_AD2:.2f} V"
        ))
        
    except ValueError:
        result_label.config(text="Please enter valid numeric values.")


       
       
def run():
    global RF_params

    RF_params = {
        "Frequency": freq,
        "Amplitude": amplitude,
        "TE": TE,
        "Tp": Tp,
        "Npulse": Npulse,
        "sampFreq": sampFreq,
        "Tacq": Tacq,
        "Resolution": resolution,
        "T_ramp": T_ramp,
        "Num_averages": num_averages,
        "Filtering": filtering,
        "Window": window,
        "Gradient": gradient,
        "Shim": shim
        }
    filename = "Recent"
    save_params_to_csv(filename)
    root.destroy()        
def previous_values():
    filename = "Recent"
    load_params_from_csv(filename)
    try:
        if RF_params:  # Check if RF_params is not empty
            frequency_var.set(str(RF_params.get('Frequency', '') / 1e6))
            amplitude_var.set(str(RF_params.get('Amplitude', '')))
            te_var.set(str(RF_params.get('TE', '') / 1e-3))
            tp_var.set(str(RF_params.get('Tp', '') /1e-6))
            Npulse_var.set(str(RF_params.get('Npulse', '')))
            sampFreq_var.set(str(RF_params.get('sampFreq', '')))
            Tacq_var.set(str(RF_params.get('Tacq', '') / 1e-3))
            resolution_var.set(str(RF_params.get('Resolution', '') / 1e-3))
            T_ramp_var.set(str(RF_params.get('T_ramp', '') / 1e-3))
            num_averages_var.set(str(RF_params.get('Num_averages', '')))
            filtering_var.set(RF_params.get('Filtering', False))
            window_var.set(RF_params.get('Window', False))
            gradient_var.set(RF_params.get('Gradient', False))
            shim_var.set(RF_params.get('Shim', False))
        else:
            result_label.config(text="No previous values found.")
    except ValueError:
        result_label.config(text="Invalid Previous Values.")

def open_save_window():
    global RF_params
    update_values()
    RF_params = {
        "Frequency": freq,
        "Amplitude": amplitude,
        "TE": TE,
        "Tp": Tp,
        "Npulse": Npulse,
        "sampFreq": sampFreq,
        "Tacq": Tacq,
        "Resolution": resolution,
        "T_ramp": T_ramp,
        "Num_averages": num_averages,
        "Filtering": filtering,
        "Window": window,
        "Gradient": gradient,
        "Shim": shim
        }
    # Create a new top-level window
    save_window = tk.Toplevel(root)
    save_window.title("Save Parameters")
    save_window.geometry("300x100")
    
    # Label and entry for the filename
    tk.Label(save_window, text="Enter Filename:").pack(pady=5)
    filename_var = tk.StringVar()
    filename_entry = tk.Entry(save_window, textvariable=filename_var)
    filename_entry.pack(pady=5)
    
    # Function to save with the specified filename
    def save_with_filename():
        filename = filename_var.get().strip()
        if filename:
            save_params_to_csv(filename)
            save_window.destroy()
            result_label.config(text=f"Parameters saved to {filename}.csv")
    
    # Accept button to save and close the window
    accept_button = tk.Button(save_window, text="Accept", command=save_with_filename)
    accept_button.pack(pady=5)

def load_saved_parameters():
    filename = filedialog.askopenfilename(
        title="Select Parameter File",
        filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
    )
    if filename:
        base_filename = os.path.basename(filename)
        load_params_from_csv(base_filename[:-4])
        try:
            if RF_params:  # Check if RF_params is not empty
                frequency_var.set(str(RF_params.get('Frequency', '') / 1e6))
                amplitude_var.set(str(RF_params.get('Amplitude', '')))
                te_var.set(str(RF_params.get('TE', '') / 1e-3))
                tp_var.set(str(RF_params.get('Tp', '') /1e-6))
                Npulse_var.set(str(RF_params.get('Npulse', '')))
                sampFreq_var.set(str(RF_params.get('sampFreq', '')))
                Tacq_var.set(str(RF_params.get('Tacq', '') / 1e-3))
                resolution_var.set(str(RF_params.get('Resolution', '') / 1e-3))
                T_ramp_var.set(str(RF_params.get('T_ramp', '') / 1e-3))
                num_averages_var.set(str(RF_params.get('Num_averages', '')))
                filtering_var.set(RF_params.get('Filtering', False))
                window_var.set(RF_params.get('Window', False))
                gradient_var.set(RF_params.get('Gradient', False))
                shim_var.set(RF_params.get('Shim', False))
            else:
                result_label.config(text="No previous values found.")
        except ValueError:
            result_label.config(text="Invalid Previous Values.")
        result_label.config(text=f"Parameters loaded from {base_filename[:-4]}")

# Create the main window
root = tk.Tk()
root.title("Parameter Input")


# Create Tkinter variables
frequency_var = tk.StringVar(value="3.34")
amplitude_var = tk.StringVar(value="1")
te_var = tk.StringVar(value="10")
tp_var = tk.StringVar(value="25")
Npulse_var = tk.StringVar(value="2")
sampFreq_var = tk.StringVar(value ="1000000")
Tacq_var = tk.StringVar(value = "8.192")
resolution_var = tk.StringVar(value = "333")
T_ramp_var = tk.StringVar(value = '5')
num_averages_var = tk.StringVar(value = '1')
filtering_var = tk.BooleanVar(value=True)
window_var = tk.BooleanVar(value=True)
gradient_var = tk.BooleanVar(value=True)
shim_var = tk.BooleanVar(value=True)
echo_filename_var = tk.StringVar(value = "echo")

# Trace changes in the input variables
frequency_var.trace("w", update_values)
amplitude_var.trace("w", update_values)
te_var.trace("w", update_values)
tp_var.trace("w", update_values)
Npulse_var.trace("w", update_values)
sampFreq_var.trace("w", update_values)
Tacq_var.trace("w", update_values)
resolution_var.trace("w", update_values)
T_ramp_var.trace("w", update_values)
num_averages_var.trace("w", update_values)
filtering_var.trace("w", update_values)
window_var.trace("w", update_values)
gradient_var.trace("w", update_values)
shim_var.trace("w", update_values)
echo_filename_var.trace("w", update_values)

# Create labels and entries for each parameter
tk.Label(root, text="Frequency (MHz):").grid(row=0, column=0)
frequency_entry = tk.Entry(root, textvariable=frequency_var)
frequency_entry.grid(row=0, column=1)

tk.Label(root, text="Amplitude (V):").grid(row=1, column=0)
amplitude_entry = tk.Entry(root, textvariable=amplitude_var)
amplitude_entry.grid(row=1, column=1)

tk.Label(root, text="TE (ms):").grid(row=2, column=0)
te_entry = tk.Entry(root, textvariable=te_var)
te_entry.grid(row=2, column=1)

tk.Label(root, text="Tp (us):").grid(row=3, column=0)
tp_entry = tk.Entry(root, textvariable=tp_var)
tp_entry.grid(row=3, column=1)

tk.Label(root, text="Npulse:").grid(row=4, column=0)
Npulse_entry = tk.Entry(root, textvariable=Npulse_var)
Npulse_entry.grid(row=4, column=1)

tk.Label(root, text="sampFreq:").grid(row=5, column=0)
sampFreq_entry = tk.Entry(root, textvariable=sampFreq_var)
sampFreq_entry.grid(row=5, column=1)

tk.Label(root, text="Tacq (ms):").grid(row=6, column=0)
Tacq_entry = tk.Entry(root, textvariable=Tacq_var)
Tacq_entry.grid(row=6, column=1)

tk.Label(root, text="Resolution (mm):").grid(row=7, column=0)
Resolution_entry = tk.Entry(root, textvariable=resolution_var)
Resolution_entry.grid(row=7, column=1)

tk.Label(root, text="T_ramp (ms):").grid(row=8, column=0)
T_ramp_entry = tk.Entry(root, textvariable=T_ramp_var)
T_ramp_entry.grid(row=8, column=1)

tk.Label(root, text="Num Averages:").grid(row=9, column=0)
num_averages_entry = tk.Entry(root, textvariable=num_averages_var)
num_averages_entry.grid(row=9, column=1)


# Create a label for the filtering option
filtering_label = tk.Label(root, text="Filtering:")
filtering_label.grid(row=10, column=0)

# Create a checkbox to toggle filtering option
filtering_checkbox = tk.Checkbutton(root, variable=filtering_var, justify=tk.LEFT)
filtering_checkbox.grid(row=10, column=1)


# Create a label for the windowing option
window_label = tk.Label(root, text="Window:")
window_label.grid(row=11, column=0)

# Create a checkbox to toggle windowing option
window_checkbox = tk.Checkbutton(root, variable=window_var, justify=tk.LEFT)
window_checkbox.grid(row=11, column=1)

# Create a label for the gradient option
gradient_label = tk.Label(root, text="Gradient:")
gradient_label.grid(row=12, column=0)

# Create a checkbox to toggle gradient option
gradient_checkbox = tk.Checkbutton(root, variable=gradient_var, justify=tk.LEFT)
gradient_checkbox.grid(row=12, column=1)

# Create a label for the shim option
shim_label = tk.Label(root, text="Shim:")
shim_label.grid(row=13, column=0)

# Create a checkbox to toggle shim option
shim_checkbox = tk.Checkbutton(root, variable=shim_var, justify=tk.LEFT)
shim_checkbox.grid(row=13, column=1)

# Label to show the result
result_label = tk.Label(root, text="", justify=tk.LEFT)
result_label.grid(row=0, column=2, columnspan=2)

tk.Label(root, text="Echo File Name:").grid(row=8, column=2)
echo_filename_entry = tk.Entry(root, textvariable=echo_filename_var)
echo_filename_entry.grid(row=9, column=2)


# Create a button to execute the calculations
run_button = tk.Button(root, text="Run", command=run)
run_button.grid(row=17, columnspan=2)

prev_values = tk.Button(root, text="Load Previous Parameters", command=previous_values)
prev_values.grid(row=16, columnspan=2)

# Create button to open save window
save_button = tk.Button(root, text="Save Current Parameters", command=open_save_window)
save_button.grid(row=14, columnspan=2)

# Create button to load saved parameters from a file
load_button = tk.Button(root, text="Load Saved Parameters", command=load_saved_parameters)
load_button.grid(row=15, columnspan=2)

# Start the main event loop
update_values()  # Call to display initial values
root.mainloop()


###################################################################
       # Opens the AD2s
##################################################################
Trig_AD2 = 3*predelay+2.5*Tp-(Tacq/2)   #  trigger the AD2 digitizer 2 msec after the start
SeqTime = .04    # duration that will encompass a single pulse sequence
DIO_rate = 10**5  # effective clock rate of the digital i/O
totalCycles = SeqTime*DIO_rate

##   Hide the open_ad2 code by by left click next to the if statement
open_ad2 = 1
prt_info = 1
if open_ad2 == 1:
    dwf = cdll.dwf
    # check library loading errors, like: Adept Runtime not found
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    # declare ctype variables
    IsInUse = c_bool()
    hdwf = c_int()
    rghdwf = []
    cchannel = c_int()
    cdevices = c_int()
    voltage = c_double();
    sts = c_byte()
    hzAcq = c_double(sampFreq)  # changes sample frequency into c_double
    rgdSamples = (c_double * numSamp)()  # list for C1 on scope
    # declare string variables
    devicename = create_string_buffer(64)
    serialnum = create_string_buffer(16)
  
    # enumerate connected devices
    dwf.FDwfEnum(c_int(0), byref(cdevices))
#            print ("Number of Devices: "+str(cdevices.value))
    
    # open and configure devices
    for idevice in range(0, cdevices.value):
        dwf.FDwfEnumDeviceName(c_int(idevice), devicename)
        dwf.FDwfEnumSN(c_int(idevice), serialnum)
        if (prt_info == 1):
          print ("------------------------------")
    #              print (' idevice = ',idevice)
          print ("Device "+str(idevice+1)+" : ")
          print ('Serial Number = ',serialnum.value)
        dwf.FDwfDeviceOpen(c_int(idevice), byref(hdwf))
        if hdwf.value == 0:
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            print (szerr.value)
            dwf.FDwfDeviceCloseAll()
            sys.exit(0)
            
        rghdwf.append(hdwf.value)           
    # looks up buffer size
        cBufMax = c_int()
        dwf.FDwfAnalogInBufferSizeInfo(hdwf, 0, byref(cBufMax))
        
        dwf.FDwfEnumDeviceName(c_int(idevice), devicename)
        dwf.FDwfEnumSN(c_int(idevice), serialnum)
        hdwf.value = rghdwf[idevice]
    # configure and start clock
    hzSys = c_double()
    dwf.FDwfDigitalOutInternalClockInfo(hdwf, byref(hzSys))
#  Finished setting up multiple AD2s


###################################################################
       # DIO Lines
##################################################################
set_ad2_device(0)

# Setup External Scope trigger
Trig_low = .0001
Trig_high = .001
y = set_dio(0,totalCycles,Trig_low,Trig_high)

# Setup AD2 Scope trigger
Trig_low = Trig_AD2
Trig_high = Tacq
y = set_dio(4,totalCycles,Trig_low,Trig_high)

#T/R Switch

Trig_low_2 = predelay- (50e-6)
Trig_high_2 = 2*Tp + (predelay + 110e-6)
y3 = set_dio(2,totalCycles,Trig_low_2,Trig_high_2)


#Attenuator
Trig_low_3 = 2*predelay
Trig_high_3 = Tp*3
y4 = set_dio(3,totalCycles,Trig_low_3,Trig_high_3)
################################################################
################################################################



###################################################################
       # Phase Encoding
##################################################################


Npe = 32
Gpe_max = V_AD2
Phase_encode_steps = np.linspace(-Gpe_max, Gpe_max, Npe)
Phase_encode_steps += np.min(np.abs(Phase_encode_steps))

for n in range(0, Npe):
    
    
   ###################################################################
          # Gradient Code
   ################################################################## 
   
   
    hzFreq2 = 1e3
    cSamples = 4096
    T_end = predelay + (Tp/2) + TE + (Tacq/2) + T_ramp
    time_grad = np.linspace(0,T_end, cSamples)
    dwell = T_end / cSamples
    gradiant_voltage = V_AD2
    #hdwf = c_int()
    rgdSamples2 = (c_double*cSamples)()
    GxWFRM = (c_double*cSamples)()

    # Channel 1 Gradient
    channel = c_int(1)
    gradient_scale = -1
    gradient_scale /= 5
    if gradient == 1:
        #Phase Encode Pulse Ramp Up
        for i in range(int((predelay+Tp)/dwell), int((predelay + Tp + T_ramp) / dwell) + 1 ):
            rgdSamples2[i] = (Phase_encode_steps[n])*((i-int((predelay+Tp)/dwell))/int(T_ramp/dwell))
        
        #Phase Encode Pulse straight
        for i in range(int((predelay + Tp + T_ramp) / dwell), int((predelay + Tp + T_ramp + (Tacq/2)) / dwell) + 1 ):
            rgdSamples2[i] = (Phase_encode_steps[n])
        
        #Phase Encode Pulse Ramp Down
        for i in range(int((predelay + Tp + T_ramp + (Tacq/2)) / dwell), int((predelay + Tp + (2*T_ramp) + (Tacq/2)) / dwell)):
            rgdSamples2[i] = -(Phase_encode_steps[n])*(((i+1)-int((predelay + Tp + (2*T_ramp) + (Tacq/2)) / dwell))/int(T_ramp/dwell))
             
        #Phase Encode Pulse Ramp Up
        for i in range(int((predelay+Tp)/dwell), int((predelay + Tp + T_ramp) / dwell) + 1 ):
            GxWFRM[i] = (Phase_encode_steps[n])*((i-int((predelay+Tp)/dwell))/int(T_ramp/dwell))
        
        #Phase Encode Pulse straight
        for i in range(int((predelay + Tp + T_ramp) / dwell), int((predelay + Tp + T_ramp + (Tacq/2)) / dwell) + 1 ):
            GxWFRM[i] = (Phase_encode_steps[n])
        
        #Phase Encode Pulse Ramp Down
        for i in range(int((predelay + Tp + T_ramp + (Tacq/2)) / dwell), int((predelay + Tp + (2*T_ramp) + (Tacq/2)) / dwell)):
            GxWFRM[i] = -(Phase_encode_steps[n])*(((i+1)-int((predelay + Tp + (2*T_ramp) + (Tacq/2)) / dwell))/int(T_ramp/dwell))        

        for i in range(0, len(GxWFRM)):
            GxWFRM[i] = GxWFRM[i] * gradient_scale
        hzFreq2 = 1/dwell/cSamples
        set_ad2_device(1)
        dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_int(1))
        dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcCustom) 
        dwf.FDwfAnalogOutNodeDataSet(hdwf, channel, AnalogOutNodeCarrier, GxWFRM, c_int(cSamples))
        dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(hzFreq2)) 
        dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(5.0)) 
        
        dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(1.0/hzFreq2)) # run for 2 periods
        dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(1)) # repeat 3 times
        dwf.FDwfAnalogOutTriggerSourceSet(hdwf, channel, trigsrcExternal1)  # sets the trigger source
        
        
    # Channel 0 Gradient Frequency Encoding
    channel = c_int(0)
    gradient_scale = 2.2
    gradient_scale /= 5
    if gradient == 1:
        #Dephase Pulse Ramp Up
        for i in range(int((predelay+Tp)/dwell), int((predelay + Tp + T_ramp) / dwell) + 1 ):
            rgdSamples2[i] = (gradiant_voltage)*((i-int((predelay+Tp)/dwell))/int(T_ramp/dwell))
        
        #Dephase Pulse straight
        for i in range(int((predelay + Tp + T_ramp) / dwell), int((predelay + Tp + T_ramp + (Tacq/2)) / dwell) + 1 ):
            rgdSamples2[i] = (gradiant_voltage)
        
        #Dephase Pulse Ramp Down
        for i in range(int((predelay + Tp + T_ramp + (Tacq/2)) / dwell), int((predelay + Tp + (2*T_ramp) + (Tacq/2)) / dwell)):
            rgdSamples2[i] = -(gradiant_voltage)*(((i+1)-int((predelay + Tp + (2*T_ramp) + (Tacq/2)) / dwell))/int(T_ramp/dwell))
        
        #Readout Pulse Ramp Up
        for i in range(int((predelay+(Tp/2) + TE - (Tacq/2) -T_ramp)/dwell), int((predelay+(Tp/2) + TE - (Tacq/2))/dwell) + 1):
            rgdSamples2[i] = (gradiant_voltage)*((i-int((predelay+(Tp/2) + TE - (Tacq/2) -T_ramp)/dwell))/int(T_ramp/dwell))
        
        #Readout Pulse straight
        for i in range(int((predelay+(Tp/2) + TE - (Tacq/2))/dwell), int((predelay+(Tp/2) + TE + (Tacq/2))/dwell) + 1):
            rgdSamples2[i] = (gradiant_voltage)
        
        #Dephase Pulse Ramp Down
        for i in range(int((predelay+(Tp/2) + TE + (Tacq/2))/dwell), int((predelay+(Tp/2) + TE + (Tacq/2) + (T_ramp))/dwell)):
            rgdSamples2[i] = -(gradiant_voltage)*(((i+1)-int((predelay+(Tp/2) + TE + (Tacq/2) + (T_ramp))/dwell))/int(T_ramp/dwell))


        GzWFRM = rgdSamples2        

        for i in range(0, len(GzWFRM)):
            GzWFRM[i] = GzWFRM[i] * gradient_scale
        
        plt.figure()
        plt.plot(time_grad, GxWFRM, label= "Phase Encode")
        plt.plot(time_grad, GzWFRM, label= "Frequency Encode")
        plt.legend()
        plt.show()

        hzFreq2 = 1/dwell/cSamples
        set_ad2_device(1)
        dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_int(1))
        dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcCustom) 
        dwf.FDwfAnalogOutNodeDataSet(hdwf, channel, AnalogOutNodeCarrier, GzWFRM, c_int(cSamples))
        dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(hzFreq2)) 
        dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(5.0)) 
        
        dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(1.0/hzFreq2)) # run for 2 periods
        dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(1)) # repeat 3 times
        dwf.FDwfAnalogOutTriggerSourceSet(hdwf, channel, trigsrcExternal1)  # sets the trigger source
    ########################################################################
    set_ad2_device(0)
    set_pos_powersupply(5)
    ########################################################################

    #SHIMMING

    def set_shim(ChNum,offset):
        dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(ChNum), c_int(1))
        dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(ChNum), funcDC) # Function
        dwf.FDwfAnalogOutOffsetSet(hdwf, c_int(ChNum), c_double(offset))
        y = 0
        return y

    # X shim
    offset0 = 0.0
    # Z shim
    offset1 = 0.0
    if shim and abs(offset0) <= 0.2 and abs(offset1) <= 0.2:
        y1 = set_ad2_device(1) # point at AD2 #2
        y1 = set_shim(0,offset0) # Set offset on channel 0 to offset0
        y1 = set_shim(1,offset1) # Set offset on channel 1 to offset1
        y1 = set_ad2_device(0) # point back to AD2 #1
    ########################################################################

    # set up acquisition (scope) (Lab 2)
    delay = 0.0

    # Set up the RF pulse generator
    y1 = set_wavegen(0,freq,amplitude,Tp,predelay,Npulse)
    #Actual TE
    Echo_time = 3*predelay+2.5*Tp-(Tacq/2)
    print(f"Time to Echo: {Echo_time}")
    #LO
    IF = 200e3
    y1 = set_wavegen(1,(freq-IF),amplitude,Tacq,Echo_time,1)
    y1 = set_scope(sampFreq,numSamp,Tacq,delay) 
    # Arm the analog and digital sections 
        # Arm the analog and digital sections 
    y1 = set_ad2_device(1)
    y1 = arm_dio(SeqTime)
    y1 = arm_analog()
    y1 = set_ad2_device(0)
    y1 = arm_dio(SeqTime)
    y1 = arm_analog()
    time.sleep(0.25)
    ## Found the below was needed. Trigger_and_read_ch0 configures channel 0.
    y1 = set_ad2_device(1)
    dwf.FDwfDigitalOutConfigure(hdwf, c_int(1))
    y1 = set_ad2_device(0)
    y1 = trigger_and_read_ch0(rgdSamples,numSamp)

    fft_data = fft(rgdSamples)
    ##Sampling time
    time2 = np.linspace(0, Tacq * 1000, num=numSamp)
    # Save the filtered signfal to a CSV file
    data = np.column_stack((time2, rgdSamples))
    np.savetxt(f'{echo_filename}.csv', data, delimiter=',', header='Samples', comments='')
    averaged_fft = np.zeros_like(fft_data, dtype=complex)
    
    
    
    for i in range(0, num_averages +1):
        
        # set up acquisition (scope) (Lab 2)
        delay = 0.0
        y1 = set_scope(sampFreq,numSamp,Tacq,delay) 
        # Arm the analog and digital sections 
            # Arm the analog and digital sections 
        y1 = set_ad2_device(1)
        y1 = arm_dio(SeqTime)
        y1 = arm_analog()
        y1 = set_ad2_device(0)
        y1 = arm_dio(SeqTime)
        y1 = arm_analog()
        time.sleep(0.25)
        ## Found the below was needed. Trigger_and_read_ch0 configures channel 0.
        y1 = set_ad2_device(1)
        dwf.FDwfDigitalOutConfigure(hdwf, c_int(1))
        y1 = set_ad2_device(0)
        y1 = trigger_and_read_ch0(rgdSamples,numSamp)
        
            
        
            
        if filtering:
            #Bandpass filter parameters
            lowCut = 2*(IF-40e3)/(sampFreq)
            highCut = 2*(IF+40e3)/(sampFreq)
            order = 6
            ripple_stop = 40 #dB
                
            #Bandpassfilter
            b, a = cheby2(order, ripple_stop, [lowCut, highCut], btype = "band", analog=False)
            rgdSamples_filt = filtfilt(b, a, rgdSamples)
                
            #Windowing
            rgdSamples_hamming = rgdSamples_filt * np.hamming(len(rgdSamples_filt))
                
            fft_values = fft(rgdSamples_hamming)
            fft_freqs = fftfreq(len(rgdSamples_hamming), 1/sampFreq)
            
        averaged_fft += fft_values
        plt.show()
    averaged_fft /= num_averages 


    # Save the projection to a TXT file
    np.savetxt(f'phase_encode_data_{n}_v1.txt', averaged_fft, delimiter='\t', header='Samples', comments='')

     #### SNR of Signal #####
    
    # signal_peak = np.max(fft_freqs)
    # std_noise = np.std(fft_freqs[len(fft_freqs)//9:len(fft_freqs)//8])
    # SNR_signal = signal_peak / std_noise
    # print(f"SNR of Echo: {SNR_signal}")
    
    
    ### Linewidth ###
    Lower = np.where(fft_freqs == IF-10e3)
    Upper = np.where(fft_freqs == IF + 10e3)
    full_spectrum = np.abs(averaged_fft[Lower[0][0]:Upper[0][0]])
    fft_freqs = fft_freqs[Lower[0][0]:Upper[0][0]]
    
    # peak_value = np.max(full_spectrum)
    # peak_freq_idx = np.argmax(full_spectrum)
    # peak_freq = averaged_fft[peak_freq_idx]
    
    # half_max = peak_value / 2
    # for i in range(len(full_spectrum)):
    #     if full_spectrum[peak_freq_idx + i] <= half_max:
    #         right_idx = i + peak_freq_idx
    #         break
    # for i in range(len(full_spectrum)):
    #     if full_spectrum[peak_freq_idx - i] <= half_max:
    #         left_idx = peak_freq_idx - i
    #         break
        
    # linewidth_hz = fft_freqs[right_idx] - fft_freqs[left_idx]    
    # linewidth_ppm = linewidth_hz / freq
    
    
    # print(f"Linewidth of Echo: {linewidth_hz} hz")
    # print(f"Linewidth of Echo: {linewidth_ppm} ppm")
    
    # Projection
    plt.figure()
    plt.plot(fft_freqs, full_spectrum, label='Projection')
    # plt.axvline(x=fft_freqs[left_idx] , color = 'orange', linestyle='--')
    # plt.axvline(x=fft_freqs[right_idx] , color = 'orange', linestyle='--')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Magnitude')
    plt.title(f'Projection #{n+1}')
    plt.grid()
    plt.legend()


    # Plot Real FFT
    # Plot Imaginary FFT
    fft_imag = np.imag(averaged_fft)
    fft_real = np.real(averaged_fft)
    fft_freqs = fftfreq(len(rgdSamples_hamming), 1/sampFreq)
    
    plt.figure()
    plt.plot(fft_freqs, fft_real, label='FFT_Real')
    plt.plot(fft_freqs, fft_imag, label='FFT_Imag')
    plt.xlabel('Frequency [Hz]')
    plt.xlim(IF-10e3, IF+10e3)
    plt.ylabel('Magnitude')
    plt.title(f'Projection #{n+1} Real')
    plt.grid()
    plt.legend()
    plt.show()
    
y1 = reset_and_close()