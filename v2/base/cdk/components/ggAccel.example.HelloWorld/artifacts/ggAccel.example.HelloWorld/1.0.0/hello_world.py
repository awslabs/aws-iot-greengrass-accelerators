import sys
import datetime

message = "Hello, %s! Current time: %s." % (sys.argv[1], datetime.datetime.now())

# Print the message to stdout.
print(message)

# Append the message to the log file.
with open("/tmp/Greengrass_HelloWorld.log", "a") as f:
    print(message, file=f)