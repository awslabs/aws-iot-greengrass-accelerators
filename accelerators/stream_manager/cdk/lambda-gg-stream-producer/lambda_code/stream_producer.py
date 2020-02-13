# Greengrass lambda source - stream producer

import os
import json
import greengrasssdk
from greengrasssdk.stream_manager import (
    StreamManagerClient,
    ReadMessagesOptions,
    NotEnoughMessagesException,
    MessageStreamDefinition,
    StrategyOnFull,
    ExportDefinition,
    IoTAnalyticsConfig,
    InvalidRequestException,
    StreamManagerException,
    Persistence,
)

channel_name = os.environ["STREAM_MANAGER_CHANNEL"]
client = StreamManagerClient()


try:
    # The LocalDataStream is low priority source for incoming sensor data and
    # aggregator function. 
    client.create_message_stream(
        MessageStreamDefinition(
            name="LocalDataStream",  # Required.
            max_size=268435456,  # Default is 256 MB.
            stream_segment_size=16777216,  # Default is 16 MB.
            time_to_live_millis=None,  # By default, no TTL is enabled.
            strategy_on_full=StrategyOnFull.OverwriteOldestData,  # Required.
            persistence=Persistence.File,  # Default is File.
            flush_on_write=False,  # Default is false.
            export_definition=ExportDefinition(
                iot_analytics=[
                    IoTAnalyticsConfig(
                        identifier="RawData",
                        iot_channel=channel_name,
                        # iot_msg_id_prefix="test",
                        # batch_size=1,
                        # batch_interval_millis=1000,
                        # priority=1
                    )
                ]
            ),
        )
    )
except StreamManagerException as e:
    print(f"Error creating message stream: {e}")
    pass
except Exception as e:
    print(f"General exception error: {e}")
    pass

def main(event, context):
    """Invoked per incoming message"""
    print(f"Event data is: {event}")
    try:
        # Incoming event is already byte encoded
        client.append_message(stream_name="LocalDataStream", data=event)
    except Exception as e:
        print(f"Error appending: {e}")
    return
