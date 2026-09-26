import re
import sys
import time
from pathlib import Path

import serial


MIN_FREE_HEAP = 2500


def ampy_config():
    config = {}
    for line in Path(".ampy").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config


config = ampy_config()
port = config["AMPY_PORT"]
baud = int(config.get("AMPY_BAUD", "115200"))
connection = serial.Serial(port, baud, timeout=0.2)

connection.write(b"\r\x03\x03")
time.sleep(0.5)
connection.reset_input_buffer()
connection.write(b"\x04")

deadline = time.monotonic() + 20
marker_seen_at = None
output = bytearray()
while time.monotonic() < deadline:
    output.extend(connection.read(1024))
    if marker_seen_at is None and b"Free heap running:" in output:
        marker_seen_at = time.monotonic()
    if marker_seen_at is not None and time.monotonic() - marker_seen_at >= 3:
        break

connection.close()
log = output.decode("utf-8", "replace")
print(log)

if "Traceback" in log or "MemoryError" in log:
    sys.exit("Cold boot failed")

match = re.search(r"Free heap running:\s*(\d+)", log)
if not match:
    sys.exit("Cold boot did not reach main loop")

free_heap = int(match.group(1))
if free_heap < MIN_FREE_HEAP:
    sys.exit("Cold boot has only {} bytes free; minimum is {}".format(
        free_heap, MIN_FREE_HEAP))

print("Cold boot passed with {} bytes free".format(free_heap))
