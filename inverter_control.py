# =================================================================================
# SIMPLE BATTERY CONTROLLER (File: inverter_control.py)
# =================================================================================
import logging
from pymodbus.client.sync import ModbusTcpClient as InverterClient

# --- Basic Configuration ---
INVERTER_IP = "192.168.178.2"  # <<< EDIT THIS TO YOUR INVERTER'S IP ADDRESS

# --- Logging Setup for clean output ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def set_inverter_register(register, value):
    try:
        client = InverterClient(INVERTER_IP, port=502)
        if not client.connect():
            logging.error(f"Failed to connect to inverter at {INVERTER_IP}.")
            return False
        result = client.write_register(register, value, unit=1)
        client.close()
        if result.isError():
            logging.error(f"Failed to write to register {register}.")
            return False
        else:
            logging.info(f"Successfully wrote value {value} to register {register}.")
            return True
    except Exception as e:
        logging.error(f"An error occurred while communicating with the inverter: {e}")
        return False

def charge_from_grid(kw: float):
    if not -0.1 < kw <= 4.5:
        logging.warning(f"Power value {kw} kW is out of a typical range. Please check the value.")
    logging.info(f"ACTION: Charging battery from grid with {kw:.2f} kW.")
    value_watts = int(-(kw * 1000))
    value_16bit = value_watts & 0xFFFF
    set_inverter_register(40355, value_16bit)
    set_inverter_register(40348, 2)

def discharge_to_grid(kw: float):
    if not 0 < kw <= 4.5:
        logging.warning(f"Discharge power {kw} kW is out of a typical range. Please check.")
    logging.info(f"ACTION: Discharging battery to grid with {kw:.2f} kW.")
    value_watts = int(kw * 1000)
    set_inverter_register(40355, value_watts)
    set_inverter_register(40348, 3)

def dont_discharge_battery():
    logging.info("ACTION: Preventing battery from discharging (0 kW charge command).")
    charge_from_grid(0)

def normal():
    logging.info("ACTION: Setting inverter to normal operating mode.")
    set_inverter_register(40355, 0)
    set_inverter_register(40348, 0)

def get_battery_percentage(inverter_ip: str) -> float | None:
    BATTERY_SOC_REGISTER = 40351
    MODBUS_PORT = 502
    MODBUS_UNIT_ID = 1
    try:
        client = InverterClient(inverter_ip, port=MODBUS_PORT)
        if not client.connect():
            logging.error(f"Failed to connect to the inverter at {inverter_ip}")
            return None
        result = client.read_holding_registers(BATTERY_SOC_REGISTER, 1, unit=MODBUS_UNIT_ID)
        client.close()
        if result.isError():
            logging.error(f"Modbus error when reading register: {result}")
            return None
        raw_soc_value = result.registers[0]
        percentage = raw_soc_value / 100.0
        logging.info(f"Successfully read battery SoC: {percentage}%")
        return percentage
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None
