import os
import re


def get_sort_key(filename):
    # Extract the digit before the dot in the filename
    match = re.search(r'(\d+)\.', filename)
    if match:
        return int(match.group(1))
    return 0


def combine_files(directory, extension, output_file, name_starting_with):
    # Get the list of files in the directory with the given extension and starting with 'log'
    files = sorted([f for f in os.listdir(directory) if f.startswith(name_starting_with) and f.endswith(extension) and os.path.isfile(os.path.join(directory, f))])

    # Sort the files by the digit in their name after 'log' and before the dot
    files.sort(key=get_sort_key)

    output_file = os.path.join(directory, output_file)

    # Open the output file in binary write mode
    with open(output_file, 'wb') as outfile:
        for filename in files:
            filepath = os.path.join(directory, filename)
            print(f'Combining {filename}...')
            # Open each file in binary read mode and write its contents to the output file
            with open(filepath, 'rb') as infile:
                outfile.write(infile.read())


# Usage example
directory = 'C:\\Users\\xxx\\Desktop\\LOGS'
# name_starting_with = 'log'
# extension = '.bin'  # Replace with the desired extension
name_starting_with = '00'
extension = '.BIN'  # Replace with the desired extension
output_file = 'combined_log.bin'
combine_files(directory, extension, output_file, name_starting_with)
