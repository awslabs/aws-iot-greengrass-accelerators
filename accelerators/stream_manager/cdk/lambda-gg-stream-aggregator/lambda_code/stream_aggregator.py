"""
    stream aggregator - Read from local data stream, aggregate data, write
                        to aggregate stream (which it turn send to defined Kinesis Data Stream)
"""
import os
import json
import logging
from time import sleep, time
from statistics import mean
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
logger.setLevel(logging.DEBUG)

LOCAL_STREAM = os.environ["LOCAL_DATA_STREAM"]
AGGREGATE_STREAM = "AggregateDataStream"
kinesis_data_stream = os.environ["KINESIS_DATA_STREAM"]
client = StreamManagerClient()
last_read_seq_num = -1


def read_from_stream(client, msg_count=10, read_timeout_millis=5000):
    """Read a batch of messages from a stream"""
    global last_read_seq_num
    messages = client.read_messages(
        LOCAL_STREAM,
        ReadMessagesOptions(
            desired_start_sequence_number=last_read_seq_num + 1,
            min_message_count=msg_count,
            read_timeout_millis=read_timeout_millis,
        ),
    )
    logger.info(f"Successfully read {len(messages)}")
    last_read_seq_num = messages[-1].sequence_number

    def extend_data(m):
        d = json.loads(m.payload)
        d.update({"sequence_number": m.sequence_number})
        return d

    return list(map(extend_data, messages))


def _get_current_epoch_millis():
    """Expand epoch time in seconds to milliseconds"""
    return round(time() * 1000)


def read_from_stream_aggregate_and_publish(client: StreamManagerClient):
    """Read the higher precision local data stream, aggregate, and publish to the aggregate stream"""
    raw_stream_data = read_from_stream(
        # Source data is ~10mps, so read 5 seconds worth (50)
        client=client,
        msg_count=50,
        read_timeout_millis=5000,
    )
    aggregated_data = {
        "avg_temperature": mean(map(lambda m: m["temperature"], raw_stream_data)),
        "avg_hertz": mean(map(lambda m: m["hertz"], raw_stream_data)),
        "timestamp": max(map(lambda m: m["timestamp"], raw_stream_data)),
        "last_sequence_number": max(
            map(lambda m: m["sequence_number"], raw_stream_data)
        ),
    }
    retries = 3
    backoff = 0.2

    # Try appending data up to 3 times. If that fails, then just move on.
    for tryNum in range(retries):
        try:
            sequence_number = client.append_message(
                AGGREGATE_STREAM, json.dumps(aggregated_data).encode("utf-8")
            )
            logger.info(
                "Successfully appended aggregated data as sequence number %d",
                sequence_number,
            )
            break
        except Exception:
            logger.warning(
                "Exception while trying to append aggregated data. Try %d of %d.",
                tryNum,
                retries,
                exc_info=True,
            )
            sleep(backoff)


# First wait until LocalDataStream is available
try:
    while True:
        stream_names = client.list_streams()
        if LOCAL_STREAM in stream_names:
            break
        logger.warning(
            f"Target consumer stream {LOCAL_STREAM} not found, pausing 1 second..."
        )
        sleep(1)
    logger.info(f"Found target consumer stream {LOCAL_STREAM}")
    pass
except Exception as e:
    print(f"Some error: {e}")

# Create AggregateDataStream to Kinesis
try:
    # The Aggregate data stream is a high priority source for aggregate data
    # sent to Kinesis Data Streams.
    client.create_message_stream(
        MessageStreamDefinition(
            name=AGGREGATE_STREAM,  # Required.
            # max_size=268435456,  # Default is 256 MB.
            # stream_segment_size=16777216,  # Default is 16 MB.
            # time_to_live_millis=None,  # By default, no TTL is enabled.
            strategy_on_full=StrategyOnFull.OverwriteOldestData,  # Required.
            # persistence=Persistence.File,  # Default is File.
            # flush_on_write=False,  # Default is false.
            export_definition=ExportDefinition(
                kinesis=[
                    KinesisConfig(
                        identifier="AggregateData",
                        kinesis_stream_name=kinesis_data_stream,
                        # Highest priority
                        priority=1,
                        batch_size=5,
                    )
                ]
            ),
        )
    )
    logger.info(
        f"Created aggregate producer stream: AggregateDataStream, with target producer Kinesis Data Stream: {kinesis_data_stream}"
    )
except StreamManagerException as e:
    logger.error(f"Error creating message stream: {e}")
    pass
except Exception as e:
    logger.error(f"General exception error: {e}")
    pass

while True:
    # Read the local data stream, aggregate, and publish forever
    try:
        read_from_stream_aggregate_and_publish(client)
    except NotEnoughMessagesException:
        pass


def main(event, context):
    """Called per invoke, we should never see this used"""
    return
