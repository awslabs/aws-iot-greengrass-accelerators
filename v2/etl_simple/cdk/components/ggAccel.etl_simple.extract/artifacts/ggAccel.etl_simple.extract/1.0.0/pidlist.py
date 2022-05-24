# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# In its current form, this code is not fit for production workloads.

"""List of OBD-II parameter Id's to query"""

from can import Message

# List of OBD-II parameter Ids to query
PIDS = {
    "vehicle_speed": Message(
        arbitration_id=0x7DF,
        is_extended_id=False,
        data=[0x2, 0x1, 0xD, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "engine_load": Message(
        arbitration_id=0x7DF,
        is_extended_id=False,
        data=[0x2, 0x1, 0x4, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "coolant_temp": Message(
        arbitration_id=0x7DF,
        is_extended_id=False,
        data=[0x2, 0x1, 0x5, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "engine_rpm": Message(
        arbitration_id=0x7DF,
        is_extended_id=False,
        data=[0x2, 0x1, 0xC, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "throttle_position": Message(
        arbitration_id=0x7DF,
        is_extended_id=False,
        data=[0x2, 0x1, 0x11, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
    "ambient_air_temperature": Message(
        arbitration_id=0x7DF,
        is_extended_id=False,
        data=[0x2, 0x1, 0x46, 0x55, 0x55, 0x55, 0x55, 0x55],
    ),
}
