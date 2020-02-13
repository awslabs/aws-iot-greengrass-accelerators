"""
    stream aggregator - Read from local data stream, aggregate data, write
                        to aggregate stream (which it turn send to defined Kinesis Data Stream)
"""
import os
import json
import logging
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

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.WARN)

# TODO - replace with KDS
# channel_name = os.environ["STREAM_MANAGER_CHANNEL"]
client = StreamManagerClient()

# First wait until LocalDataStream is available
try:
    stream_names = client.list_streams()
    print(f"stream names returned: {stream_names}")
    pass
except Exception as e:
    print(f"Some error: {e}")

# Now create AggregateDataStream
# try:
#     # The LocalDataStream is low priority source for incoming sensor data and
#     # aggregator function. 
#     client.create_message_stream(
#         MessageStreamDefinition(
#             name="LocalDataStream",  # Required.
#             max_size=268435456,  # Default is 256 MB.
#             stream_segment_size=16777216,  # Default is 16 MB.
#             time_to_live_millis=None,  # By default, no TTL is enabled.
#             strategy_on_full=StrategyOnFull.OverwriteOldestData,  # Required.
#             persistence=Persistence.File,  # Default is File.
#             flush_on_write=False,  # Default is false.
#             export_definition=ExportDefinition(
#                 iot_analytics=[
#                     IoTAnalyticsConfig(
#                         identifier="RawData",
#                         iot_channel=channel_name,
#                         # iot_msg_id_prefix="test",
#                         # batch_size=1,
#                         # batch_interval_millis=1000,
#                         # priority=1
#                     )
#                 ]
#             ),
#         )
#     )
# except StreamManagerException as e:
#     logger.error(f"Error creating message stream: {e}")
#     pass
# except Exception as e:
#     logger.error(f"General exception error: {e}")
#     pass



# While True loop for reading from Local and writing to aggregate
# read every 5 seconds worth of records, average
# Write average values to agg stream


def main(event, context):
    """Called per invoke, we should never see this used"""

    return
