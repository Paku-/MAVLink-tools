#!/usr/bin/env python3

import time
from pymavlink import mavutil
import os
import argparse
from datetime import datetime


def connect_to_drone(udp_address="192.168.4.1:14550"):
    """Establish a UDP connection to the ArduPilot drone."""
    print(f"Connecting to drone at {udp_address} via UDP...")
    connection_string = f"udp:{udp_address}"
    connection = mavutil.mavlink_connection(
        connection_string, source_system=255)
    connection.wait_heartbeat(timeout=10)  # Increased timeout for UDP
    print("Heartbeat received. Connected to drone.")
    return connection


def request_log_list(connection):
    """Request the list of available logs from the drone."""
    connection.mav.log_request_list_send(
        connection.target_system,
        connection.target_component,
        0,  # Start at log ID 0
        0xFFFF  # Request all logs (max ID)
    )
    logs = []
    while True:
        msg = connection.recv_match(type='LOG_ENTRY', blocking=True, timeout=5)
        if msg is None:
            print("Timed out waiting for LOG_ENTRY. Assuming all logs received.")
            break
        if msg.id == 0 and msg.num_logs == 0:
            print("No logs available.")
            break
        logs.append({
            'id': msg.id,
            'size': msg.size,
            'time_utc': msg.time_utc
        })
    # Sort by ID, newest first
    return sorted(logs, key=lambda x: x['id'], reverse=True)


def download_log(connection, log_id, log_size, output_dir="logs", retries=3, verbose=False):
    """Download a specific log file by ID and save it as a .bin file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Add a timestamp to the filename to make it unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/log_{log_id}_{timestamp}.bin"
    print(f"Downloading log {log_id} ({log_size} bytes) to {filename}...")

    chunk_size = 90  # MAVLink max payload for LOG_DATA is ~90 bytes
    offset = 0
    log_data = bytearray()

    for attempt in range(retries):
        while offset < log_size:
            connection.mav.log_request_data_send(
                connection.target_system,
                connection.target_component,
                log_id,
                offset,
                chunk_size
            )
            msg = connection.recv_match(
                type='LOG_DATA', blocking=True, timeout=5)
            if msg is None:
                print(
                    f"Timeout waiting for LOG_DATA for log {log_id}. Retrying...")
                break
            if msg.id != log_id:
                print(f"Received wrong log ID: {msg.id} (expected {log_id}).")
                continue
            log_data.extend(msg.data[:msg.length])
            offset += msg.length
            if verbose:
                print(
                    f"Progress: {offset}/{log_size} bytes ({(offset/log_size)*100:.1f}%)")

        if offset >= log_size:
            break
        else:
            print(
                f"Retrying download for log {log_id} (attempt {attempt + 1}/{retries})...")
            offset = 0  # Reset offset for retry
            log_data = bytearray()

    if offset < log_size:
        print(f"Failed to download log {log_id} after {retries} attempts.")
        return

    # Write the log to a .bin file
    with open(filename, 'wb') as f:
        f.write(log_data[:log_size])  # Trim to exact size
    print(f"Log {log_id} downloaded successfully.")


def download_last_n_logs(udp_address="192.168.4.1:14550", num_logs=3, retries=3, verbose=False):
    """Download the last n logs from the drone over UDP."""
    connection = connect_to_drone(udp_address)
    log_list = request_log_list(connection)

    if not log_list:
        print("No logs found on the drone.")
        return

    print(
        f"Found {len(log_list)} logs. Downloading the last {min(num_logs, len(log_list))}...")
    for log in log_list[:num_logs]:  # Take the last n logs (highest IDs)
        download_log(connection, log['id'], log['size'],
                     retries=retries, verbose=verbose)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Download logs from an ArduPilot drone.")
    parser.add_argument("--udp_address", type=str, default="192.168.4.1:14550",
                        help="UDP address of the drone (default: 192.168.4.1:14550)")
    parser.add_argument("--num_logs", type=int, default=3,
                        help="Number of logs to download (default: 3)")
    parser.add_argument("--retries", type=int, default=3,
                        help="Number of retries for failed downloads (default: 3)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output for download progress")
    args = parser.parse_args()

    # Call the main function with parsed arguments
    download_last_n_logs(args.udp_address, args.num_logs,
                         args.retries, args.verbose)
