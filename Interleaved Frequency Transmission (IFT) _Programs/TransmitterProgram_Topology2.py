import sys
from time import sleep, time
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from PIL import Image
import io
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
# Eliminate GPIO channel already in use warnings
BOARD.setup()

# Function to convert image into binary format (IO Stream)
def convert_image_to_binary(image_path):
    image = Image.open(image_path)
    image_stream = io.BytesIO()
    image.save(image_stream, format='JPEG', quality=85)
    image_data = image_stream.getvalue()
    # Convert to an array of 8-bit numbers (binary format)
    binary_data = [byte for byte in image_data]
    return binary_data

# Transmitter class
class LoRaImageTransmitter(LoRa):
    def __init__(self, verbose=False):
        super(LoRaImageTransmitter, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)  # Sleep to save power
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])
        self.set_freq(915.0)  # Set the initial operating frequency
        print(self.get_freq())

    def start(self):
        # Start the transmission
        self.write_payload([])
        self.set_mode(MODE.TX)

        # Convert image to binary data
        binary_data = convert_image_to_binary("Image3.jpg")
        
        # Define chunk size for LoRa transmission
        chunk_size = 240  # Adjust as per packet size limit
        start_time = time()  # Record start time
        
        freq_alt_ctr = 0
        print(f"Length of data to be semt: {len(binary_data)}")
        # Transmit data in chunks
        for i in range(0, len(binary_data), chunk_size):
            chunk = binary_data[i:i + chunk_size]
            #print(i)
            #print(f"Sending chunk: {chunk}")

            # Alternate frequencies: 915 MHz for even chunks, 914.5 MHz for odd chunks
            if i % (2 * chunk_size) == 0:
            #if freq_alt_ctr % 2 == 0:
                #print(915)
                self.set_mode(MODE.SLEEP)
                self.set_freq(915.0)
            else:
                #print(914.5)
                self.set_mode(MODE.SLEEP)
                self.set_freq(914.5)

            freq_alt_ctr += 1
            self.write_payload(chunk)
            self.set_mode(MODE.TX)
            sleep(0.5)  # Adjust as necessary for timing

        print(f"i last value: {i}")
        print(f"length of image data: {len(binary_data)}")
            
        # Send "ABC" as the end signal at both frequencies
        self.set_mode(MODE.SLEEP)
        self.set_freq(915.0)
        self.write_payload([0x41, 0x42, 0x43])  # "ABC"
        self.set_mode(MODE.TX)
        sleep(0.5)
        
        self.set_mode(MODE.SLEEP)
        self.set_freq(914.5)
        self.write_payload([0x41, 0x42, 0x43])  # "ABC"
        self.set_mode(MODE.TX)
        
        end_time = time()  # Record end time
        transmission_time = end_time - start_time  # Calculate time taken for transmission
        
        print(f"Time taken for transmission: {transmission_time:.2f} seconds")
        sys.exit("Sending Completed")

# Initialize LoRa transmitter
lora = LoRaImageTransmitter(verbose=False)
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
