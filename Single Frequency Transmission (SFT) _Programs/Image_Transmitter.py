import sys
from time import sleep, time
from SX127x.LoRa import *
from SX127x.board_config import BOARD
# import the python libraries
from PIL import Image
import io
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
#Eliminate GPIO channel already in use warnings
BOARD.setup()


class LoRaImageTransmitter(LoRa):

    def __init__(self, verbose=False):
        super(LoRaImageTransmitter, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        # sleep to save power
        self.set_dio_mapping([1,0,0,0,0,0])
        self.set_freq(915.0)    # Set operating frequency
        print(self.get_freq())

    def start(self):
        #global args
        self.write_payload([])
        self.set_mode(MODE.TX)
        while True:
            sleep(1)

    def on_tx_done(self):
        self.set_mode(MODE.STDBY)
        self.clear_irq_flags(TxDone=1)
        sys.stdout.flush()
        sleep(2)
        def con_b_to_i(data):
            return[int(byte)for byte in data]
        
        #Use JPEG Compression to encode message before sending
        image = Image.open("Image1.jpg")
        image_stream = io.BytesIO()
        image.save(image_stream,format='JPEG',quality=85)
        image_data = image_stream.getvalue()

        chunk_size = 240 # maximum number of bytes to send in one LoRa packet
        start_time = time()  # Record start time
        # break data into chunks and send each chunk
        for i in range(0,len(image_data),chunk_size):
            chunk = image_data[i:i+chunk_size]
            chunk_int_list = con_b_to_i(chunk)
            print(chunk)
            self.write_payload(chunk_int_list)
            self.set_mode(MODE.TX)
            sleep(1)

        #add a unique identifier to final chunk
        self.write_payload([0x41,0x42,0x43])# add ABC at the end
        self.set_mode(MODE.TX)
        
        end_time = time()  # Record end time
        transmission_time = end_time - start_time  # Calculate time taken for transmission
        
        print(f"Time taken for transmission: {transmission_time:.2f} seconds")
                                       
        sys.exit("Sending Completed") # All image packets are sent

lora = LoRaImageTransmitter(verbose=False)

lora.set_pa_config(pa_select=1)


assert(lora.get_agc_auto_on() == 1)

try: sleep(0.001)
except: pass

try:
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    sys.stderr.write("KeyboardInterrupt\n")
  #print the transmitted values on the console and terminate the program using a keyboard interrupt
finally:
     sys.stdout.flush()
     lora.set_mode(MODE.SLEEP)
     BOARD.teardown()

  
