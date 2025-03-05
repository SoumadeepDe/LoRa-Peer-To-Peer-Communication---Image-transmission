import sys
from time import sleep
from SX127x.LoRa import *
from SX127x.board_config import BOARD
import serial
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
BOARD.setup()
# Setup Ready to Receive - Jumper pin number == GPI0 23
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize UART for communication with the master
uart = serial.Serial('/dev/serial0', baudrate=115200, timeout=1000)

# Variables for storing received data
final_data = bytearray()
rssi_values = []

# Slave receiver class
class LoRaImageReceiver(LoRa):
    def __init__(self, verbose=False):
        super(LoRaImageReceiver, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)  # Sleep to save power
        self.set_dio_mapping([0, 0, 0, 0, 0, 0])
        self.set_freq(914.5)    # Set operating frequency for slave
        print(self.get_freq())

    def start(self):
        self.set_mode(MODE.RXCONT)  # Continuous receiving mode
        print("Slave receiving started...")
        
        while True:
            sleep(0.5)
            status = self.get_modem_status()
            sys.stdout.flush()

    def on_rx_done(self):
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        print(f"payload: {payload}")
        global rssi_values
        rssi_value = self.get_rssi_value()  # Get the RSSI value for the current packet
        print(f"rssi: {rssi_value}")
        rssi_values.append(rssi_value)  # Store the RSSI value for later calculation
        global final_data

        # Append the received data to the final_data
        final_data.extend(payload)

        # If the end marker (ABC) is found, send data to the master
        if b"ABC" in final_data:
            print("End marker received on slave, waiting 1 second before sending data...")
            sleep(1)  # Wait for 1 second
            
            print(f"Length of payload received: {len(final_data)}")

            self.UART_SendData()
            
            
    def UART_SendData(self):
            
            decimal_values = list(final_data)
            
            string_decimal_values = ' '.join(map(str, decimal_values))
            
            string_rssi_values = ' '.join(map(str, rssi_values))
            
            string_final_data_with_rssi = string_decimal_values + "\n" + string_rssi_values
            
            print(f"Length of data: {len(string_final_data_with_rssi)}")
            
            uart_buffer_byte_size = 4096
            
            for cntr in range(0, len(string_final_data_with_rssi), uart_buffer_byte_size):
                while (GPIO.input(23) == GPIO.LOW):
                    print("RTR LOW....")
                    
                #print(f"sending UART data: {string_final_data_with_rssi[cntr:(cntr + uart_buffer_byte_size)].encode()}")
                uart.write(string_final_data_with_rssi[cntr:(cntr + uart_buffer_byte_size)].encode())
                #sleep(0.5)
            
            sys.exit("Slave finished sending data.")
            
    
    
# Initialize LoRa receiver
lora = LoRaImageReceiver(verbose=False)
lora.set_pa_config(pa_select=1)

assert(lora.get_agc_auto_on() == 1)

try:
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()

