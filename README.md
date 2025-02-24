# LoRa Communication for Image Transmission - Topology 1 & Topology 2

This repository contains the source code, algorithms, and wiring diagrams for a **LoRa communication system** using **Raspberry Pi Zero** devices equipped with **SX1276 LoRa modules** to transmit and receive image data. The system is designed to demonstrate two topologies for efficient image transmission: **Topology 1** and **Topology 2**.

## Project Overview

The project demonstrates how to send and receive images over long distances using LoRa communication. The image is divided into smaller packets and transmitted from a **transmitter** to a **receiver**. Two topologies are implemented:

- **Topology 1 (1 Transmitter --- 1 Receiver)**: A simple point-to-point communication model.
- **Topology 2 (1 Transmitter --- 2 Receivers)**: Utilizes two receivers operating on different frequencies to reduce transmission time by enabling parallel data reception.

### Topology 1

In **Topology 1**, the system consists of a single transmitter and a single receiver. The image is split into packets, and each packet is transmitted sequentially. The receiver listens for these packets, reconstructs the image, and saves or displays it.

#### Algorithm Overview for Topology 1:
1. The transmitter compresses the image and divides it into 240-byte packets.
2. The transmitter sends each packet sequentially.
3. The receiver receives the packets and reconstructs the image after receiving the **“ABC”** marker.
4. Performance metrics such as **RSSI**, **SNR**, **BER**, and **PRR** are calculated by the receiver.

### Topology 2

In **Topology 2**, the system consists of one transmitter and two receivers that operate at different frequencies: **915 MHz for the master receiver** and **914.5 MHz for the slave receiver**. This setup allows the transmitter to send packets concurrently to both receivers, thereby reducing the overall transmission time.

#### Algorithm Overview for Topology 2:
1. The transmitter alternates between the two frequencies, sending even-indexed packets to the master and odd-indexed packets to the slave.
2. The receiver waits for the **“ABC”** marker to signify the end of the transmission.
3. The slave sends its data to the master receiver via **UART**.
4. The master receiver combines the data from both receivers and reconstructs the image.

### Challenges Addressed in Topology 2:
- **4096-byte UART buffer** limitation: Topology 2 ensures data is transferred at a rate that prevents buffer overflow by using **Ready to Receive (RTR) logic**, which synchronizes the data flow between the master and slave.

