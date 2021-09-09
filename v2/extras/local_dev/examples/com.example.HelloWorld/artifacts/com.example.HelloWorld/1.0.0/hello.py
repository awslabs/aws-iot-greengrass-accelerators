import sys
import datetime

message = f"Hello, {sys.argv[1]}! Current time: {str(datetime.datetime.now())}."
message += " Greetings from your first Greengrass component."
# Print the message to stdout.
print(message)
# Append the message to the log file.
with open("Greengrass_HelloWorld.log", "a") as f:
    print(message, file=f)
