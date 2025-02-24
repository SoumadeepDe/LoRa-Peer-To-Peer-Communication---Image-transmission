import sys
from time import sleep
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from PIL import Image
import io
# import the python libraries
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
#Eliminate GPIO Channel already in use warnings

final_data = b""
rssi_values =[]
BOARD.setup()
# is used to set the board and LoRa parameters

class LoRaRcvCont(LoRa):
    def __init__(self, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        # sleep to save power
        self.set_freq(915.0) #Set ISM Frequency band for system
        self.set_dio_mapping([0,0,0,0,0,0])

    # Calculate Average RSSI for Transmitted Packets
    def calculate_rssi_average(self):
        if rssi_values:
            rssi_average = sum(rssi_values)/len(rssi_values)
            return rssi_average
        return None

    # Calculate Signal-to-Noise Ratio(SNR) for  Packets
    def calculate_snr(self):
        rssi = self.calculate_rssi_average()
        noise_power = -122.9
        snr = rssi - noise_power
        return snr
    
    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(.5)
        status = self.get_modem_status()
        sys.stdout.flush()
     
    def on_rx_done(self):
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        rssi_value = self.get_rssi_value()
        rssi_values.append(rssi_value)
        print("RSSI: ",rssi_value)
        global final_data

        # get executed data after the incoming packet is read
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
         
        global final_data
        final_data += bytes(payload)

        if b"ABC" in final_data:

            # Calculate Bit Error Rate (BER)
            sent_data = b""
            with open("pics/Image1.jpg", "rb") as file:
                sent_data = file.read()
            total_bits = len(sent_data) * 8
            error_bits = sum((x != y) for x, y in zip(sent_data, final_data))
            ber = error_bits / total_bits
            print("Bit Error Rate (BER): {:.3f}".format(ber))

            #Calculate the Packet Reception Rate(PRR)
            PRR = (1-ber)*100
            print("% of Correct Packets: {:.3f}".format(PRR))

            # Save received data as an image with JPEG Compression
            with open("ReceivedJ1.jpg", "wb") as f:
                f.write(final_data)
                print("Image saved as Received.jpg")
            # Get average RSSI and SNR values
            rssi_average = self.calculate_rssi_average()
            if rssi_average is not None:
                print("Average RSSI: {:.3f} ".format(rssi_average))
            snr = self.calculate_snr()
            print("SNR: {:.3f} ".format(snr))

lora = LoRaRcvCont(verbose=False)

lora.set_mode(MODE.STDBY)
lora.set_pa_config(pa_select=1)

assert(lora.get_agc_auto_on() == 1)

try: 
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    sys.stderr.write("KeyboardInterrupt\n")
#print the received values on the console and terminate the program using a keyboard interrupt
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
    
 