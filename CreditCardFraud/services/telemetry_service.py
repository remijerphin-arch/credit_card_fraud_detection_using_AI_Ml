import datetime

class TelemetryStore:
    latest = None

def update_telemetry(device_id, battery=None, rssi=None, firmware=None, is_simulated=False):
    """Updates the active device telemetry store with live connection metadata."""
    TelemetryStore.latest = {
        "device_id": device_id,
        "status": "Active" if not is_simulated else "Simulated",
        "connection": "Connected (API Push)" if not is_simulated else "Simulation Mode",
        "last_communication": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "battery": f"{battery}%" if battery is not None else "95% (Battery)",
        "rssi": f"{rssi} dBm" if rssi is not None else "-62 dBm",
        "firmware": firmware if firmware is not None else "v1.0.0-rc1",
        "last_payload": f"Card: {device_id}"
    }

def get_telemetry():
    """Fetches the latest telemetry or returns offline defaults if no device is connected."""
    if TelemetryStore.latest is None:
        return {
            "device_id": "N/A",
            "status": "Offline",
            "connection": "Waiting for Device",
            "last_communication": "Never",
            "firmware": "N/A",
            "battery": "N/A",
            "rssi": "N/A",
            "last_payload": "None"
        }
    return TelemetryStore.latest
