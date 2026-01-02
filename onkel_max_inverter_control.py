# =================================================================================
# SIMPLE BATTERY CONTROLLER - HUAWEI LUNA2000 (File: huawei_inverter_control.py)
# =================================================================================
import logging
from pymodbus.client.sync import ModbusTcpClient as InverterClient

# --- Grundkonfiguration ---
# HIER DEINE DATEN EINTRAGEN
# ---------------------------------
INVERTER_IP = "192.168.178.2"  # <<< EDITIEREN: IP-Adresse deines Wechselrichters
INVERTER_PORT = 6607  # <<< WICHTIG: Huawei nutzt oft Port 6607 für Schreibzugriff
MODBUS_UNIT_ID = 1  # <<< WICHTIG: Bei Huawei oft 1 (manchmal 0)
# ---------------------------------

# --- Logging-Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Huawei Modbus-Register (können je nach Firmware leicht variieren) ---
# Register für Lade-/Entladeleistung (Forcible charge/discharge power)
REG_SET_POWER_WATTS = 47082
# Register für Modus (0=Stop, 1=Laden, 2=Entladen)
REG_SET_MODE = 47075
# Register für Batterie-SoC (in 0.1%)
REG_GET_BATTERY_SOC = 37760


def set_inverter_register(register, value):
    """
    Schreibt einen einzelnen Wert in ein Register des Wechselrichters.
    """
    try:
        client = InverterClient(INVERTER_IP, port=INVERTER_PORT)
        if not client.connect():
            logging.error(f"Fehler beim Verbinden mit dem Wechselrichter unter {INVERTER_IP}:{INVERTER_PORT}.")
            return False

        logging.debug(f"Schreibe auf Register {register} den Wert {value} (Unit ID: {MODBUS_UNIT_ID})")
        # Schreibe auf die angegebene Unit ID
        result = client.write_register(register, value, unit=MODBUS_UNIT_ID)
        client.close()

        if result.isError():
            logging.error(f"Fehler beim Schreiben auf Register {register}: {result}")
            return False
        else:
            logging.info(f"Erfolgreich Wert {value} auf Register {register} geschrieben.")
            return True
    except Exception as e:
        logging.error(f"Ein Fehler ist bei der Modbus-Kommunikation aufgetreten: {e}")
        return False


def charge_from_grid(kw: float):
    """
    Weist den Wechselrichter an, die Batterie aus dem Netz mit X kW zu laden.
    """
    if not 0 <= kw <= 10:  # Huawei kann oft bis zu 10kW
        logging.warning(f"Leistungswert {kw} kW ist außerhalb des normalen Bereichs (0-10 kW).")

    logging.info(f"AKTION: Lade Batterie aus dem Netz mit {kw:.2f} kW.")
    value_watts = int(kw * 1000)

    # 1. Leistung setzen (z.B. 2500W)
    set_inverter_register(REG_SET_POWER_WATTS, value_watts)
    # 2. Modus auf "Laden" (1) setzen
    set_inverter_register(REG_SET_MODE, 1)


def discharge_to_grid(kw: float):
    """
    Weist den Wechselrichter an, die Batterie ins Netz mit X kW zu entladen.
    """
    if not 0 < kw <= 10:
        logging.warning(f"Entladeleistung {kw} kW ist außerhalb des normalen Bereichs (0-10 kW).")

    logging.info(f"AKTION: Entlade Batterie ins Netz mit {kw:.2f} kW.")
    value_watts = int(kw * 1000)

    # 1. Leistung setzen (z.B. 2500W)
    set_inverter_register(REG_SET_POWER_WATTS, value_watts)
    # 2. Modus auf "Entladen" (2) setzen
    set_inverter_register(REG_SET_MODE, 2)


def dont_discharge_battery():
    """
    Verhindert, dass die Batterie entladen wird.
    Setzt den Lademodus auf "Laden" mit 0 kW.
    """
    logging.info("AKTION: Batterieentladung verhindern (0 kW Ladebefehl).")
    # Setzt den Modus auf "Laden" (1) mit 0W Leistung
    charge_from_grid(0)


def normal():
    """
    Setzt den Wechselrichter in den normalen (automatischen) Betriebsmodus.
    Stoppt "Forcible Charge/Discharge".
    """
    logging.info("AKTION: Wechselrichter in Normalbetrieb setzen (stoppe Zwangsladung/-entladung).")
    # 1. Leistung auf 0 setzen (sicherheitshalber)
    set_inverter_register(REG_SET_POWER_WATTS, 0)
    # 2. Modus auf "Stop" (0) setzen
    set_inverter_register(REG_SET_MODE, 0)


def get_battery_percentage(inverter_ip: str) -> float | None:
    """
    Liest den aktuellen Ladezustand (SoC) der Batterie.
    """
    try:
        client = InverterClient(inverter_ip, port=INVERTER_PORT)
        if not client.connect():
            logging.error(f"Fehler beim Verbinden mit dem Wechselrichter unter {inverter_ip}")
            return None

        # Lese 1 Register ab der Startadresse, von der richtigen Unit ID
        result = client.read_holding_registers(REG_GET_BATTERY_SOC, 1, unit=MODBUS_UNIT_ID)
        client.close()

        if result.isError():
            logging.error(f"Modbus-Fehler beim Lesen von Register {REG_GET_BATTERY_SOC}: {result}")
            return None

        raw_soc_value = result.registers[0]
        # Huawei liefert den SoC in 0.1%, daher durch 10.0 teilen
        percentage = raw_soc_value / 10.0

        logging.info(f"Batterie-SoC erfolgreich gelesen: {percentage}% (Rohwert: {raw_soc_value})")
        return percentage
    except Exception as e:
        logging.error(f"Ein unerwarteter Fehler beim Lesen des SoC ist aufgetreten: {e}")
        return None


# --- Beispielaufrufe (zum Testen auskommentieren) ---
if __name__ == "__main__":
    logging.info("Starte Inverter Control Test...")

    # Test 1: SoC auslesen
    soc = get_battery_percentage(INVERTER_IP)
    if soc is not None:
        logging.info(f"Aktueller Batterie-SoC: {soc}%")
    else:
        logging.warning("Konnte SoC nicht auslesen. Überprüfe Verbindung und Einstellungen.")

    # --- VORSICHT: DIE FOLGENDEN BEFEHLE STEUERN DEINEN WECHSELRICHTER ---
    # --- Nur einzeln und mit Bedacht testen! ---

    # Test 2: Wechselrichter auf "Normal" setzen
    # normal()

    # Test 3: Batterie mit 0.5 kW aus dem Netz laden
    # import time
    # charge_from_grid(0.5)
    # time.sleep(30) # 30 Sekunden laden
    # normal() # Unbedingt wieder auf normal setzen!

    # Test 4: Batterie mit 0.2 kW ins Netz entladen
    # import time
    # discharge_to_grid(0.2)
    # time.sleep(30) # 30 Sekunden entladen
    # normal() # Unbedingt wieder auf normal setzen!

    logging.info("Inverter Control Test beendet.")