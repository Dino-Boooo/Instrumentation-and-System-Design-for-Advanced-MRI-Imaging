"""Spin-echo acquisition and resonance search.

Plays a two-pulse spin-echo sequence from AD2 #1, captures the echo with the
acquisition window centered on it, and plots the raw signal, its FFT, and the
band-pass filtered, Hamming-windowed result (saved to echo.csv and
filtered_signal.csv).

The frequency-sweep block at the end of the file (3.30-3.34 MHz in 2 kHz steps)
is disabled; enable it to search for the resonance on a new magnet setup.

Built on the MR Engineering course starter code for the WaveForms SDK.
DIO pin 0 is an external scope trigger; pin 4 drives external trigger input 1
to start the AD2 digitizer.
"""

from dwfconstants import *

import sys
import matplotlib.pyplot as plt
import numpy as np
import time
from scipy.signal import cheby2, filtfilt
from scipy.fftpack import fft, fftfreq
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

frequency = 3.318e6
amplitude = 3
TE = 10e-3 #milliseconds
Tp = 250e-6
predelay = (TE/2) - Tp
Npulse = 2        
sampFreq = 1000000
Tacq = .008192
numSamp = int(Tacq * sampFreq)
Trig_AD2 = 3*predelay+2.5*Tp-(Tacq/2)   #  trigger the AD2 digitizer 2 msec after the start
SeqTime = .04    # duration that will encompass a single pulse sequence
DIO_rate = 10**5  # effective clock rate of the digital i/O
totalCycles = SeqTime*DIO_rate


filtering = True
###################################################################
       # Opens the AD2s
##################################################################


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
#############################################################

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
# Deleted the RF pulse generator from Example 1
#######   Added this code to do the custom waveform
hzFreq2 = 1e3
cSamples = 4096
#hdwf = c_int()
rgdSamples2 = (c_double*cSamples)()
# Switch channels
channel = c_int(1)

# ramp up from 0-0.5
for i in range(0,int((len(rgdSamples2))/2)):
    rgdSamples2[i] = 2.0*i/cSamples;
# ramp down from 0.5-1
for i in range(int((len(rgdSamples2))/2), len(rgdSamples2)):
    rgdSamples2[i] = (-2.0*i/cSamples) + 2;

print("Generating custom waveform...")
# dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_int(1))
# dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcCustom) 
# dwf.FDwfAnalogOutNodeDataSet(hdwf, channel, AnalogOutNodeCarrier, rgdSamples2, c_int(cSamples))
# dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(hzFreq2)) 
# dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(2)) 

# dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(1/hzFreq2)) # run for 1 periods
# dwf.FDwfAnalogOutWaitSet(hdwf, channel, c_double(3.0/hzFreq2)) # predelay of 2 sec
# dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(1)) # No repeats
# dwf.FDwfAnalogOutTriggerSourceSet(hdwf, channel, trigsrcDigitalOut)  # sets the trigger source
# #dwf.FDwfAnalogOutConfigure(hdwf, channel, c_int(1))    # This is in "arm_analog" function

########################################################################

set_pos_powersupply(5)
########################################################################

for i in range(0,1):

    # set up acquisition (scope) (Lab 2)
    delay = 0.0
    # Set up the RF pulse generator
    y1 = set_wavegen(0,frequency,amplitude,Tp,predelay,Npulse)
    
    Echo_time = 3*predelay+2.5*Tp-(Tacq/2)
    print(f"Time to Echo: {Echo_time}")
    #LO 
    y1 = set_wavegen(1,(frequency-100e3),amplitude,Tacq,Echo_time,1)
    y1 = set_scope(sampFreq,numSamp,Tacq,delay) 
    # Arm the analog and digital sections 
    y1 = arm_dio(SeqTime)
    y1 = arm_analog()       
    time.sleep(1)
    #  trigger and collect data
    print('going to trigger')
    y1 = trigger_and_read_ch0(rgdSamples,numSamp)     
    print('back from trigger')
    

    ##Sampling time
    time2 = np.linspace(0, Tacq * 1000, num=numSamp)
    # Save the unfiltered signfal to a CSV file
    data = np.column_stack((time2, rgdSamples))
    np.savetxt('echo.csv', data, delimiter=',', header='Samples', comments='')
    # Plot the sampled data
    Tacqms = Tacq * 1000.
    plt.plot(time2,rgdSamples)
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage")
    plt.title(f"{frequency} Hz")
    fig1 = plt.show()

    # FFT of echo
    fft_values = fft(rgdSamples)
    fft_freqs = fftfreq(len(rgdSamples), 1/sampFreq)
    plt.figure()
    plt.plot(fft_freqs[len(fft_freqs)//12:len(fft_freqs)//8], np.abs(fft_values)[len(fft_freqs)//12:len(fft_values)//8], label='FFT of Echo')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Magnitude')
    plt.title(f'FFT of Echo for {frequency} Hz signal')
    plt.grid()
    plt.legend()        

    if filtering:
        #Bandpass filter parameters
        lowCut = 2*(100e3-10e3)/(sampFreq)
        highCut = 2*(100e3+10e3)/(sampFreq)
        order = 2
        ripple_stop = 40 #dB
        
        #Bandpassfilter
        b, a = cheby2(order, ripple_stop, [lowCut, highCut], btype = "band", analog=False)
        rgdSamples_filt = filtfilt(b, a, rgdSamples)
    
        #Windowing
        rgdSamples_hamming = rgdSamples_filt * np.hamming(len(rgdSamples_filt))

        # Save the filtered signfal to a CSV file
        data = np.column_stack((time2, rgdSamples_hamming))
        np.savetxt('filtered_signal.csv', data, delimiter=',', header='Samples', comments='')
            
            
        # Plot the sampled data
        Tacqms = Tacq * 1000.
        plt.figure()
        plt.plot(time2,rgdSamples_hamming)
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage")
        plt.title(f"{frequency} Hz")
        fig1 = plt.show()

        # FFT of echo
        fft_values = fft(rgdSamples_hamming)
        fft_freqs = fftfreq(len(rgdSamples_hamming), 1/sampFreq)
        plt.figure()
        plt.plot(fft_freqs[len(fft_freqs)//12:len(fft_freqs)//8], np.abs(fft_values)[len(fft_freqs)//12:len(fft_values)//8], label='FFT of Echo')
        plt.xlabel('Frequency [Hz]')
        plt.ylabel('Magnitude')
        plt.title(f'FFT of Echo for {frequency} Hz signal')
        plt.grid()
        plt.legend()
    
    now = datetime.now()
    print(now)
    
    print(np.std(rgdSamples))

'''
start_freq = 3.3e6 # MHz
stop_freq = 3.34e6 # MHz
step_size = 2e3 # KHz
freq_list = np.arange(start_freq, stop_freq+1, step_size)

print(freq_list)

for freq in freq_list:
    # set up acquisition (scope) (Lab 2)
    delay = 0.0
    # Set up the RF pulse generator
    y1 = set_wavegen(0,freq,amplitude,Tp,predelay,Npulse)
    #Actual TE
    Echo_time = 3*predelay+2.5*Tp-(Tacq/2)
    print(f"Time to Echo: {Echo_time}")
    #LO 
    y1 = set_wavegen(1,(freq-100e3),amplitude,Tacq,Echo_time,1)
    y1 = set_scope(sampFreq,numSamp,Tacq,delay) 
    # Arm the analog and digital sections 
    y1 = arm_dio(SeqTime)
    y1 = arm_analog()       
    time.sleep(1)
    #  trigger and collect data
    print('going to trigger')
    print(type(rgdSamples))
    y1 = trigger_and_read_ch0(rgdSamples,numSamp)     
    print('back from trigger')
    ##Sampling time
    time2 = np.linspace(0, Tacq * 1000, num=numSamp)
    
    
    # Save the unfiltered signfal to a CSV file
    data = np.column_stack((time2, rgdSamples))
    np.savetxt('unfiltered_signal.csv', data, delimiter=',', header='Samples', comments='')
    
    if filtering:
        #Bandpass filter parameters
        lowCut = 2*(100e3-10e3)/(sampFreq)
        highCut = 2*(100e3+10e3)/(sampFreq)
        order = 2
        ripple_stop = 40 #dB
        
        #Bandpassfilter
        b, a = cheby2(order, ripple_stop, [lowCut, highCut], btype = "band", analog=False)
        rgdSamples_filt = filtfilt(b, a, rgdSamples)
        
        #Windowing
        rgdSamples_hamming = rgdSamples * np.hamming(len(rgdSamples_filt))
        
        # Save the filtered signfal to a CSV file
        data = np.column_stack((time2, rgdSamples))
        np.savetxt('filtered_signal.csv', data, delimiter=',', header='Samples', comments='')
        
        
        # Plot the sampled data
        Tacqms = Tacq * 1000.
        plt.figure()
        plt.plot(time2,rgdSamples_hamming)
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage")
        plt.title(f"{freq} Hz")
        fig1 = plt.show()

        # FFT of echo
        fft_values = fft(rgdSamples_hamming)
        fft_freqs = fftfreq(len(rgdSamples_hamming), 1/sampFreq)
        plt.figure()
        plt.plot(fft_freqs[len(fft_freqs)//12:len(fft_freqs)//8], np.abs(fft_values)[len(fft_freqs)//12:len(fft_values)//8], label='FFT of Echo')
        plt.xlabel('Frequency [Hz]')
        plt.ylabel('Magnitude')
        plt.title(f'FFT of Echo for {freq} Hz signal')
        plt.grid()
        plt.legend()
    
    else:
        # Plot the sampled data
        Tacqms = Tacq * 1000.
        plt.figure()
        plt.plot(time2,rgdSamples)
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage")
        plt.title(f"{freq} Hz")
        fig1 = plt.show()
            

        
        # FFT of echo
        fft_values = fft(rgdSamples)
        fft_freqs = fftfreq(len(rgdSamples), 1/sampFreq)
        plt.figure()
        plt.plot(fft_freqs[len(fft_freqs)//12:len(fft_freqs)//8], np.abs(fft_values)[len(fft_freqs)//12:len(fft_values)//8], label='FFT of Echo')
        plt.xlabel('Frequency [Hz]')
        plt.ylabel('Magnitude')
        plt.title(f'FFT of Echo for {freq} Hz signal')
        plt.grid()
        plt.legend()
 '''
y1 = reset_and_close()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    