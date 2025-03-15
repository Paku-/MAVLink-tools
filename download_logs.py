#!/usr/bin/env python3

import time
from pymavlink import mavutil
import os


def connect_to_drone(tcp_address="192.168.4.1:14550"):
    """Establish a TCP connection to the ArduPilot drone."""
    print(f"Connecting to drone at {tcp_address}...")
    # Use tcp: to specify a remote TCP target
    connection_string = f"tcp:{tcp_address}"
    connection = mavutil.mavlink_connection(
        connection_string, source_system=255)
    connection.wait_heartbeat(timeout=10)  # Increased timeout for TCP
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
        if msg.id == msg.last_log_num - 1:
            break
    # Sort by ID, newest first
    return sorted(logs, key=lambda x: x['id'], reverse=True)


def download_log(connection, log_id, log_size, output_dir="logs"):
    """Download a specific log file by ID and save it as a .bin file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = f"{output_dir}/log_{log_id}.bin"
    print(f"Downloading log {log_id} ({log_size} bytes) to {filename}...")

    # Request log data in chunks
    chunk_size = 90  # MAVLink max payload for LOG_DATA is ~90 bytes
    offset = 0
    log_data = bytearray()

    while offset < log_size:
        connection.mav.log_request_data_send(
            connection.target_system,
            connection.target_component,
            log_id,
            offset,
            chunk_size
        )
        msg = connection.recv_match(type='LOG_DATA', blocking=True, timeout=5)
        if msg is None:
            print(f"Timeout waiting for LOG_DATA for log {log_id}.")
            break
        if msg.id != log_id:
            print(f"Received wrong log ID: {msg.id} (expected {log_id}).")
            continue
        log_data.extend(msg.data[:msg.length])
        offset += msg.length
        print(
            f"Progress: {offset}/{log_size} bytes ({(offset/log_size)*100:.1f}%)")

    # Write the log to a .bin file
    with open(filename, 'wb') as f:
        f.write(log_data[:log_size])  # Trim to exact size
    print(f"Log {log_id} downloaded successfully.")


def download_last_n_logs(tcp_address="192.168.4.1:14550", num_logs=3):
    """Download the last n logs from the drone over TCP."""
    connection = connect_to_drone(tcp_address)
    log_list = request_log_list(connection)

    if not log_list:
        print("No logs found on the drone.")
        return

    print(
        f"Found {len(log_list)} logs. Downloading the last {min(num_logs, len(log_list))}...")
    for log in log_list[:num_logs]:  # Take the last n logs (highest IDs)
        download_log(connection, log['id'], log['size'])


if __name__ == "__main__":
    # Customize these as needed
    TCP_ADDRESS = "192.168.4.1:14550"  # Your drone's TCP address
    NUM_LOGS = 3  # Number of logs to download

    download_last_n_logs(TCP_ADDRESS, NUM_LOGS)
