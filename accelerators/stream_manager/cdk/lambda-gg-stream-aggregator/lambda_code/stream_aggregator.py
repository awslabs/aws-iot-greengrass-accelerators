"""
    stream aggregator - Read from local data stream, aggregate data, write
                        to aggregate stream (which it turn send to defined Kinesis Data Stream)
"""

import os
import json
import logging
from time import sleep
import greengrasssdk
from greengrasssdk.stream_manager import (
    StreamManagerClient,
    ReadMessagesOptions,
    NotEnoughMessagesException,
    MessageStreamDefinition,
    StrategyOnFull,
    ExportDefinition,
    KinesisConfig,
    InvalidRequestException,
    StreamManagerException,
    Persistence,
)

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.WARN)

kinesis_data_stream = os.environ["KINESIS_DATA_STREAM"]
local_stream = os.environ["LOCAL_DATA_STREAM"]
client = StreamManagerClient()

# First wait until LocalDataStream is available
try:
    while True:
        stream_names = client.list_streams()
        if local_stream in stream_names:
            break
        logger.warning(f"Target stream {local_stream} no found, pausing 1 second...")
        sleep(1)
    pass
except Exception as e:
    print(f"Some error: {e}")

# Create AggregateDataStream to Kinesis
try:
    # The LocalDataStream is low priority source for incoming sensor data and
    # aggregator function. 
    client.create_message_stream(
        MessageStreamDefinition(
            name="AggregateDataStream",  # Required.
            max_size=268435456,  # Default is 256 MB.
            stream_segment_size=16777216,  # Default is 16 MB.
            time_to_live_millis=None,  # By default, no TTL is enabled.
            strategy_on_full=StrategyOnFull.OverwriteOldestData,  # Required.
            persistence=Persistence.File,  # Default is File.
            flush_on_write=False,  # Default is false.
            export_definition=ExportDefinition(
                kinesis=[
                    KinesisConfig(
                        identifier="AggregateData",
                        kinesis_stream_name=kinesis_data_stream,
                        # Highest priority
                        priority=1
                    )
                ]
            ),
        )
    )
except StreamManagerException as e:
    logger.error(f"Error creating message stream: {e}")
    pass
except Exception as e:
    logger.error(f"General exception error: {e}")
    pass



# While True loop for reading from Local and writing to aggregate
# read every 5 seconds worth of records, average
# Write average values to agg stream


def main(event, context):
    """Called per invoke, we should never see this used"""

    return
