# BYD Battery Controller

A simple and effective web-based controller for BYD home batteries paired with a Fronius inverter. Designed to run on a lightweight device like a Raspberry Pi.

## Features

- **Web Interface**: Easy-to-use control panel.
- **Manual Control**: Charge, stop discharge, or set to normal mode.
- **Scheduling**: Schedule charging or mode changes at specific times.
- **Monitoring**: View current battery State of Charge (SoC).

## Requirements

- **Hardware**:
  - Fronius Inverter
  - BYD Battery Box
  - Raspberry Pi (or any server running Python)
- **Software**:
  - Python 3.x
  - Flask
  - APScheduler
  - PyModbus

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/jakobschw17/battery_controller.git
    cd battery_controller
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    - Open `inverter_control.py`.
    - Set your inverter's IP address:
      ```python
      INVERTER_IP = "192.168.1.X" # Replace with your IP
      ```

## Usage

1.  **Run the application:**
    ```bash
    python app.py
    ```

2.  **Access the web interface:**
    - Open your browser and navigate to `http://<raspberry-pi-ip>:5000`.

## Disclaimer

Use this software at your own risk. Incorrect use of Modbus commands can potentially harm your hardware.
