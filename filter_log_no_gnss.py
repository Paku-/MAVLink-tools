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
import sys
from collections import defaultdict
from pymavlink import mavutil
from pymavlink.dialects.v20 import ardupilotmega


def has_gps_location(message):
    """
    Check if a MAVLink message contains GNSS location data (latitude, longitude, altitude).
    Returns True if the message has GNSS location data, False otherwise.
    Safely handles messages without GNSS fields.
    """
    # Define message types that typically contain GNSS location data
    gps_messages = {
        'GPS',
        'POS',
        'ORGN',
        'TERR',
        'AHR2',
        'EAHR',
        'MISSION_ITEM',
        'GLOBAL_POSITION_INT',
        'POSITION',
        'NAV_CONTROLLER_OUTPUT',
    }

    # Get message type from the message name
    msg_type = message.get_type()

    if msg_type not in gps_messages:
        return False  # Non-GNSS messages are not filtered

    # Safely check specific fields for GNSS location data, handling missing attributes
    try:
        if msg_type == 'GPS':
            return (hasattr(message, 'Lat') and message.Lat != 0 or
                    hasattr(message, 'Lon') and message.Lon != 0)
        elif msg_type == 'POS':
            return (hasattr(message, 'Lat') and message.Lat != 0 or
                    hasattr(message, 'Lng') and message.Lon != 0)
        elif msg_type == 'ORGN':
            return (hasattr(message, 'Lat') and message.Lat != 0 or
                    hasattr(message, 'Lng') and message.Lon != 0)
        elif msg_type == 'TERR':
            return (hasattr(message, 'Lat') and message.Lat != 0 or
                    hasattr(message, 'Lng') and message.Lon != 0)
        elif msg_type == 'AHR2':
            return (hasattr(message, 'Lat') and message.Lat != 0 or
                    hasattr(message, 'Lng') and message.Lon != 0)
        elif msg_type == 'EAHR':
            return (hasattr(message, 'Lat') and message.Lat != 0 or
                    hasattr(message, 'Lon') and message.Lon != 0)
        elif msg_type == 'GLOBAL_POSITION_INT':
            return (hasattr(message, 'lat') and message.lat != 0 or
                    hasattr(message, 'lon') and message.lon != 0 or
                    hasattr(message, 'relative_alt') and message.relative_alt != 0)
        elif msg_type == 'POSITION':
            return (hasattr(message, 'Lat') and message.Lat != 0 or
                    hasattr(message, 'Lon') and message.Lon != 0 or
                    hasattr(message, 'RelAlt') and message.RelAlt != 0)
        elif msg_type == 'NAV_CONTROLLER_OUTPUT':
            return (hasattr(message, 'nav_bearing') and message.nav_bearing != 0 or
                    hasattr(message, 'target_bearing') and message.target_bearing != 0)
        elif msg_type == 'MISSION_ITEM':
            return (hasattr(message, 'x') and message.x != 0 or
                    hasattr(message, 'y') and message.y != 0)
    except AttributeError:
        return False  # If any field check fails, assume no GNSS location data


def filter_log_without_gps(input_file, output_file=None):
    """
    Read an ArduPilot binary log, filter out entries with GNSS location data,
    and save the result to a new binary log. Report removed and passed entries.
    Skip non-filter-relevant messages like PARM during packing.
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}-no-gnss{ext}"

    # Open the input log file using DFReader with ardupilotmega dialect
    mlog = mavutil.mavlink_connection(input_file, dialect='ardupilotmega')

    # Create a MAVLink instance using the ardupilotmega dialect
    mav = ardupilotmega.MAVLink(None)

    # Create or open the output log file
    with open(output_file, 'wb') as outfile:
        print(f"Processing log file: {input_file}")
        print(f"Writing filtered log to: {output_file}")

        # Initialize counters
        msg_count = 0
        removed_count = 0
        passed_count = 0
        msg_type_counts_passed = defaultdict(int)
        msg_type_counts_removed = defaultdict(int)

        # Process each message in the log
        while True:
            msg = mlog.recv_match(blocking=False)
            if msg is None:
                break  # End of file

            msg_count += 1
            msg_type = msg.get_type()

            if not has_gps_location(msg):
                # Convert DFMessage to MAVLink_message and pack it
                try:
                    outfile.write(msg.get_msgbuf())
                    passed_count += 1
                    msg_type_counts_passed[msg_type] += 1
                except Exception as e:
                    print(f"Error message {msg_type}: {e}")
                    continue
            else:
                removed_count += 1
                msg_type_counts_removed[msg_type] += 1
                print(
                    f"{removed_count}:\tRemoved message {msg_type} with GNSS location data.")

        print(f"\nProcessed {msg_count} total messages.")
        print(f"Removed {removed_count} entries with GNSS location data.")
        print(f"Passed {passed_count} entries without GNSS location data.")
        print(
            f"Saved {passed_count} non-GNSS location entries to {output_file}.")

        # Print per message type statistics
        print("\nMessage type statistics (passed):")
        for msg_type, count in sorted(msg_type_counts_passed.items(), key=lambda item: item[1], reverse=True):
            print(f"{msg_type}: {count}")

        print("\nMessage type statistics (removed):")
        for msg_type, count in sorted(msg_type_counts_removed.items(), key=lambda item: item[1], reverse=True):
            print(f"{msg_type}: {count}")


def main():
    # Get input file from command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python script.py input_log.bin [output_log.bin]")
        print("If output file is not specified, defaults to 'input_log_no_gnss.bin'")
        sys.exit(1)

    input_log = sys.argv[1]
    output_log = sys.argv[2] if len(sys.argv) > 2 else None

    filter_log_without_gps(input_log, output_log)


if __name__ == "__main__":
    main()
