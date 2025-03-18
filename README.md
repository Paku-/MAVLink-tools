# MAVLink Tools by Paku

This repository contains tools for working with MAVLink logs and interacting with ArduPilot-based drones. These scripts are designed to analyze MAVLink logs, filter specific messages, and download logs from drones.

---

## Scripts Overview

### 1. **`analyze.py`**
#### Description:
This script analyzes a MAVLink log file and provides statistics about message types and field values. It can also filter messages by type or pattern and optionally print all matching messages.

#### Usage:
```bash
python analyze.py <log_file> [--msg_name <message_type_pattern>] [--print_msgs]
```

#### Parameters:
- `<log_file>`: Path to the MAVLink log file to analyze.
- `--msg_name`: (Optional) Filter by specific message type or pattern (e.g., `GPS*`).
- `--print_msgs`: (Optional) Print all messages satisfying the conditions.

#### Examples:
- Analyze all messages in a log file:
  ```bash
  python analyze.py flight_log.bin
  ```
- Analyze only `GPS` messages:
  ```bash
  python analyze.py flight_log.bin --msg_name GPS
  ```
- Analyze and print all messages starting with `GPS`:
  ```bash
  python analyze.py flight_log.bin --msg_name GPS* --print_msgs
  ```

---

### 2. **`filter_log_no_gnss.py`**
#### Description:
This script filters out MAVLink messages containing GNSS (GPS) location data from a log file and saves the filtered log to a new file.

#### Usage:
```bash
python filter_log_no_gnss.py <input_log> [output_log]
```

#### Parameters:
- `<input_log>`: Path to the input MAVLink log file.
- `[output_log]`: (Optional) Path to save the filtered log file. Defaults to `<input_log>-no-gnss.bin`.

#### Examples:
- Filter GNSS data from a log file:
  ```bash
  python filter_log_no_gnss.py flight_log.bin
  ```
- Save the filtered log to a specific file:
  ```bash
  python filter_log_no_gnss.py flight_log.bin filtered_log.bin
  ```

---

### 3. **`download_logs.py`**
#### Description:
This script connects to an ArduPilot-based drone over UDP, retrieves a list of available logs, and downloads the last `n` logs.

#### Usage:
```bash
python download_logs.py [--udp_address <udp_address>] [--num_logs <number>] [--retries <retries>] [--verbose]
```

#### Parameters:
- `--udp_address`: (Optional) UDP address of the drone. Default: `192.168.4.1:14550`.
- `--num_logs`: (Optional) Number of logs to download. Default: `3`.
- `--retries`: (Optional) Number of retries for failed downloads. Default: `3`.
- `--verbose`: (Optional) Enable verbose output for download progress.

#### Examples:
- Download the last 3 logs (default settings):
  ```bash
  python download_logs.py
  ```
- Download the last 5 logs with verbose output:
  ```bash
  python download_logs.py --num_logs 5 --verbose
  ```
- Specify a custom UDP address and retry failed downloads 5 times:
  ```bash
  python download_logs.py --udp_address 192.168.10.1:14550 --retries 5
  ```

---

## Requirements
- Python 3.x
- `pymavlink` library
- `numpy` library (for `analyze.py`)

Install dependencies using:
```bash
pip install pymavlink numpy
```

---

## Notes
- Ensure the drone is powered on and connected to the specified network for `download_logs.py`.
- The `filter_log_no_gnss.py` script is useful for removing sensitive GNSS data from logs before sharing them.
- The `analyze.py` script supports wildcard patterns for filtering message types, making it flexible for analyzing specific subsets of data.

---

## License
This work is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0). To view a copy of this license, visit [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/).

---

## Author
Paku

