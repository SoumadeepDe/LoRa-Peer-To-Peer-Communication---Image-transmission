import sys
import serial
from time import sleep, time
from SX127x.LoRa import *
from SX127x.board_config import BOARD
from PIL import Image
import io
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
BOARD.setup()
# Setup Ready to Receive - Jumper pin number 16 == GPIO 23
GPIO.setup(23, GPIO.OUT)

# Initialize UART
uart = serial.Serial('/dev/serial0', baudrate=115200, timeout=1)

# Variables for performance metrics
final_data = bytearray()
rssi_values = []

# Master receiver class
class LoRaImageReceiver(LoRa):
    def __init__(self, verbose=False):
        super(LoRaImageReceiver, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)  # Sleep to save power
        self.set_dio_mapping([0, 0, 0, 0, 0, 0])
        self.set_freq(915.0)    # Set operating frequency
        print(self.get_freq())

    def start(self):
        self.set_mode(MODE.RXCONT)  # Continuous receiving mode
        print("Master receiving started...")
        
        while True:
            sleep(0.5)
            #self.test_please_work()
            status = self.get_modem_status()
            sys.stdout.flush()

    def on_rx_done(self):
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        print(f"Received payload: {payload}")
        global final_data
        global first_payload_chunk_size

        # If the first payload, determine the chunk size
        if not final_data:
            first_payload_chunk_size = len(payload)
            print(f"First payload received. Chunk size is: {first_payload_chunk_size}")
        
        # Append the received data to final_data
        final_data.extend(payload)

        # If the end marker (ABC) is found, process the data
        if b"ABC" in final_data:
            print("End marker received on master, waiting for slave...")
            
            start_time = time()  # Start the 10-second timer
            slave_data = bytearray()
            
            print(f"Length of data: {len(final_data)}")

            counter = 0
            temp_counter = 0
            
            GPIO.output(23, GPIO.HIGH)
            while True:
                new_data = uart.read(4096)
                GPIO.output(23, GPIO.LOW)
                #sleep(5)
                print(f"uart data: {new_data}")
                if new_data:
                    print(f"Extending: {counter}")
                    counter += 1
                    slave_data.extend(new_data)
                    temp_counter = 0
                    GPIO.output(23, GPIO.HIGH)
                else:
                    if counter == 0:
                        GPIO.output(23, GPIO.HIGH)    
                        continue
                    else:
                        if temp_counter > 5:
                            GPIO.output(23, GPIO.HIGH)
                            break
                        else:
                            temp_counter +=1
                            sleep(0.5)
                            GPIO.output(23, GPIO.HIGH)
            
            # If no data was received after 10 seconds, move on
            if not slave_data:
                print("No data received from slave within 100 seconds. Moving on.")
                sys.exit("Check connection between master and slave receiver.")
                return  # Exit or continue as needed

            #print(f"Received data from slave: {slave_data}")
            #print(f"Slave data size: {len(slave_data)}")

            # Split the received data into image data and RSSI values
            if b'\n' in slave_data:
                image_data, rssi_data = slave_data.split(b'\n', 1)

                # Clean up image data: removing extra spaces and converting to integers
                image_data = image_data.strip()  # Remove any leading/trailing whitespace
                image_data_bytes = bytearray(map(int, image_data.split()))  # Convert decimal values to bytes

                # Convert the RSSI data to a list of integers
                # Step 1: Decode the bytearray to string
                rssi_str = rssi_data.decode('utf-8')

                # Step 2: Split the string into individual values (by spaces)
                rssi_list = rssi_str.split()

                # Step 3: Convert each value to an integer
                rssi_values = [int(rssi) for rssi in rssi_list]
                #rssi_values = [int(rssi) for rssi in rssi_data.split() if rssi.isdigit()]
            else:
                print("Error: Received data does not contain expected separator")
                return

            # Determine the chunk size from the first payload (Master's first chunk)
            chunk_size = len(final_data)
            #print(f"Chunk size: {chunk_size}")
            
            #print(f"rssi values: {rssi_data}")

            # Alternate combining master and slave data
            #global combined_data
            global master_chunk
            global slave_chunk
            combined_data = bytearray()
            master_chunk = final_data[:chunk_size]
            slave_chunk = image_data_bytes[:chunk_size]            
            
            #
            #My code
            #
            master_chunk_new = bytearray()
            slave_chunk_new = bytearray()
            master_chunk_new = master_chunk[0:len(master_chunk)-3]
            slave_chunk_new = slave_chunk[0:len(slave_chunk)-3]
            print(f"length of master_chunk: {len(master_chunk_new)}")
            print(f"length of slave_chunk: {len(slave_chunk_new)}")
            #print(f"master_chunk: {master_chunk_new}")
            #print(f"slave_chunk: {slave_chunk_new}")
            combined_data_new = bytearray()
            
            if (len(slave_chunk_new) % first_payload_chunk_size) == 0:
                print("Last data on Master Freq")
                for i in range(0, int(len(slave_chunk)/first_payload_chunk_size), 1):
                    #print(f"start index: {first_payload_chunk_size * i}")
                    #print(f"end index: {(first_payload_chunk_size * (i + 1))}")
                    combined_data_new.extend(master_chunk[(first_payload_chunk_size * i) : (first_payload_chunk_size * (i + 1))])
                    combined_data_new.extend(slave_chunk[(first_payload_chunk_size * i) : (first_payload_chunk_size * (i + 1))])
                    #print(f"new combined length: {len(combined_data_new)}")
            
                #print(f"combined image: {combined_data_new}")
                #print(f"new combined length: {len(combined_data_new)}")
                i +=1
                combined_data_new.extend(master_chunk[(first_payload_chunk_size * i) : len(master_chunk_new)])
            else:
                print("Last data on Slave Freq")
                for i in range(0, int(len(slave_chunk)/first_payload_chunk_size), 1):
                    #print(f"start index: {first_payload_chunk_size * i}")
                    #print(f"end index: {(first_payload_chunk_size * (i + 1))}")
                    combined_data_new.extend(master_chunk[(first_payload_chunk_size * i) : (first_payload_chunk_size * (i + 1))])
                    combined_data_new.extend(slave_chunk[(first_payload_chunk_size * i) : (first_payload_chunk_size * (i + 1))])
                    #print(f"new combined length: {len(combined_data_new)}")
            
                #print(f"combined image: {combined_data_new}")
                #print(f"new combined length: {len(combined_data_new)}")
                i +=1
                combined_data_new.extend(master_chunk[(first_payload_chunk_size * i) : (first_payload_chunk_size * (i + 1))])
                combined_data_new.extend(slave_chunk[(first_payload_chunk_size * i) : len(slave_chunk_new)])
                 
            print(f"final data len: {len(combined_data_new)}")

            new_final_data = combined_data_new  # Store the final combined data

            # Decode the image data and display/save it
            self.decode_and_save_image(new_final_data)
            
            

            # Calculate performance metrics
            self.calculate_performance_metrics(new_final_data, rssi_values)
            

            sys.exit("Image successfully received and saved.")

        
    def decode_and_save_image(self, data):
        """ Decodes the image data and saves it as an image file """
        
        print("Decoding image...")
        try:
            # Convert the byte data into an image
            image_stream = io.BytesIO(data)
            image = Image.open(image_stream)

            # Save the image
            image.save("ReceivedImage.jpg")
            print("Image saved as 'ReceivedImage.jpg'.")

            # Optionally display the image
            image.show()
        except Exception as e:
            print(f"Error decoding the image: {e}")

    # Calculate performance metrics (RSSI, SNR, BER, PRR)
    def calculate_performance_metrics(self, decoded_data, rssi_values):
        # Calculate the average RSSI from both master and slave
        rssi_average = sum(rssi_values) / len(rssi_values) if rssi_values else 0
        print(f"Average RSSI: {rssi_average:.3f} dBm")

        # Calculate the Signal-to-Noise Ratio (SNR)
        snr = self.calculate_snr(rssi_average)
        print(f"SNR: {snr:.3f} dB")

        # Calculate Bit Error Rate (BER)
        ber = self.calculate_ber(decoded_data)
        print(f"Bit Error Rate (BER): {ber:.3f}")

        # Calculate Packet Reception Rate (PRR)
        prr = (1 - ber) * 100
        print(f"Packet Reception Rate (PRR): {prr:.3f}%")

    # Calculate Signal-to-Noise Ratio (SNR)
    def calculate_snr(self, rssi_average):
        noise_power = -122.9  # Typical noise floor in dBm for LoRa
        return rssi_average - noise_power

    # Calculate Bit Error Rate (BER)
    def calculate_ber(self, decoded_data):
        # Read the sent data (original image) for comparison
        sent_data = bytearray()
        with open("Image3.jpg", "rb") as file:
            sent_data = file.read()

        total_bits = len(sent_data) * 8
        error_bits = sum((x != y) for x, y in zip(sent_data, decoded_data))
        ber = error_bits / total_bits
        return ber

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

