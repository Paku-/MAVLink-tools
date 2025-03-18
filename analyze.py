#!/usr/bin/env python3

# This work is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).
# To view a copy of this license, visit https://creativecommons.org/licenses/by/4.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
#
# You are free to:
# - Share: copy and redistribute the material in any medium or format.
# - Adapt: remix, transform, and build upon the material for any purpose, even commercially.
#
# Under the following terms:
# - Attribution: You must give appropriate credit, provide a link to the license, and indicate if changes were made.
#
# Author: Paku
# Date: March 2025

import os
import argparse
from pymavlink import mavutil
from collections import defaultdict
import numpy as np
import fnmatch


def analyze_mavlink_log(logfile_path, msg_name=None, print_msgs=False):
    # Check if the file exists
    if not os.path.exists(logfile_path):
        print(f"Error: Log file '{logfile_path}' not found.")
        return

    # Open the MAVLink log file in binary mode
    print(f"Opening log file: {logfile_path}")
    try:
        mlog = mavutil.mavlink_connection(logfile_path)
    except Exception as e:
        print(f"Error opening log file: {e}")
        return

    # Dictionaries to store stats
    message_counts = defaultdict(int)  # Count of each message type
    # Store values for each field in each message type
    field_values = defaultdict(list)

    # Read through the log
    print("Analyzing log file...")
    msg_count = 0
    while True:
        try:
            msg = mlog.recv_msg()
            if msg is None:  # End of log
                break

            msg_count += 1
            msg_type = msg.get_type()
            if msg_type == "BAD_DATA":  # Skip malformed packets
                continue

            # If a specific message name or pattern is provided, filter messages
            if msg_name and not fnmatch.fnmatch(msg_type, msg_name):
                continue

            # Update message count
            message_counts[msg_type] += 1

            # Extract fields and store numeric values
            fields = msg.to_dict()
            for field_name, value in fields.items():
                # Skip non-numeric fields and mavpackettype
                if isinstance(value, (int, float)) and field_name != "mavpackettype":
                    field_key = f"{msg_type}.{field_name}"
                    field_values[field_key].append(value)

            # Print the message if the --print_msgs flag is set
            if print_msgs:
                print(f"Message: {msg}")

        except Exception as e:
            print(f"Error processing message: {e}")
            break

    # Prepare output with proper line endings
    output_lines = []
    output_lines.append(f"Processed {msg_count} messages.\n")
    if msg_name:
        output_lines.append(f"Filtered by message type: {msg_name}\n")
    output_lines.append("=== MAVLink Log Analysis ===\n")
    output_lines.append("Message Type Counts (sorted by packet count):\n")

    # Sort by count (descending), then by message type alphabetically for ties
    sorted_counts = sorted(message_counts.items(), key=lambda x: (-x[1], x[0]))
    for msg_type, count in sorted_counts:
        output_lines.append(f"{msg_type}: {count} messages\n")

    output_lines.append("Field Statistics (fields with non-zero average):\n")
    has_data = False
    for field_key, values in sorted(field_values.items()):
        if len(values) > 0:  # Only process fields with values
            try:
                min_val = min(values)
                max_val = max(values)
                avg_val = np.mean(values)
                # Skip if average is effectively zero (with tolerance 1e-5)
                if abs(avg_val) < 1e-5:
                    continue
                has_data = True
                output_lines.append(
                    f"{field_key}: Count={len(values)}, Min={min_val:.2f}, Max={max_val:.2f}, Average={avg_val:.2f}\n")
            except Exception as e:
                output_lines.append(f"{field_key}: Error={e}\n")

    if not has_data:
        output_lines.append("No fields with non-zero average found.\n")

    # Display on screen
    print("".join(output_lines))

    # Save to file
    output_file = logfile_path.replace('.bin', '_analysis.txt')
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("".join(output_lines))
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving to file: {e}")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Analyze a MAVLink log file.")
    parser.add_argument(
        "log_file", help="Path to the MAVLink log file to analyze.")
    parser.add_argument(
        "--msg_name", help="Filter by specific message type or pattern (e.g., 'msg*').", default=None)
    parser.add_argument(
        "--print_msgs", help="Print all messages satisfying the conditions.", action="store_true")
    args = parser.parse_args()

    # Call the analysis function with the provided log file, message name, and print_msgs flag
    analyze_mavlink_log(args.log_file, args.msg_name, args.print_msgs)


if __name__ == "__main__":
    main()
