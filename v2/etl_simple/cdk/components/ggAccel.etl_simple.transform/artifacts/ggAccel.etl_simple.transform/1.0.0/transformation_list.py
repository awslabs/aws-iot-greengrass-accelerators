"""Formulas for transforming extracted data"""
import json
import time


def obd2_convert(msg):
    """Convert OBD-II message"""

    timestamp = float(msg.split(" ")[0])
    arbitration_id = msg.split(" ")[1]
    event = bytearray.fromhex(msg.split(" ")[2])

    # 0x7E8 is CAN Bus arbitration Id for response to PID query
    if arbitration_id == "7E8":
        # Read 3rd byte for OBD-II PID
        pid = bytes(event)[2]
        if pid == 0x4:
            # Calculated engine load - % - A/2.55
            val = bytes(event)[3] / 2.55
            msg_template = {
                "Pid": "EngineLoad",
                "Value": val,
                "Units": "%",
                "Source": "OBD-II",
            }
        elif pid == 0x5:
            # Engine coolant temperature - C - A-40
            val = bytes(event)[3] - 40
            msg_template = {
                "Pid": "EngineCoolantTemperature",
                "Value": val,
                "Units": "Celsius",
                "Source": "OBD-II",
            }
        elif pid == 0xC:
            # Engine RPM - rpm - (256 * A + B)/4
            val = (bytes(event)[3] * 256 + bytes(event)[4]) / 4
            msg_template = {
                "Pid": "EngineRPM",
                "Value": val,
                "Units": "rpm",
                "Source": "OBD-II",
            }
        elif pid == 0xD:
            # Vehicle speed - km/h - A
            val = bytes(event)[3]
            msg_template = {
                "Pid": "VehicleSpeed",
                "Value": val,
                "Units": "km/h",
                "Source": "OBD-II",
            }
        elif pid == 0x11:
            # Throttle position - % - A/2.55
            val = bytes(event)[3] / 2.55
            msg_template = {
                "Pid": "ThrottlePosition",
                "Value": val,
                "Units": "%",
                "Source": "OBD-II",
            }
        elif pid == 0x46:
            # Ambient air temperature - C - A - 40
            val = bytes(event)[3] - 40
            msg_template = {
                "Pid": "AmbientAirTemperature",
                "Value": val,
                "Units": "Celsius",
                "Source": "OBD-II",
            }
        else:
            # Unknown / unsolicited OBD-II
            msg_template = {
                "Pid": "UnknownObdPid",
                "Value": pid,
                "RawMessage": msg.split(" ")[2],
                "Source": "OBD-II",
            }
    else:
        # Unknown CAN Bus arbitration Id
        msg_template = {
            "Pid": "UnknownArbitrationId",
            "Value": msg.split(" ")[1],
            "RawMessage": msg.split(" ")[2],
            "Source": "CAN Bus",
        }
    msg_template["Timestamp"] = timestamp
    return msg_template