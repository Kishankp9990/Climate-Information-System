
# #code for single data file filtration ...........................................................................................
# # Define the input and output file names
# input_file = '1159300_Q_Day.Cmd.txt'
# output_file = '1159300_Q_Day_filtered.Cmd.txt'

# # Open the input file for reading with latin-1 encoding
# with open(input_file, 'r', encoding='latin-1') as infile:
#     # Open the output file for writing
#     with open(output_file, 'w', encoding='utf-8') as outfile:
#         # Read the file line by line
#         data_section = False
#         for line in infile:
#             # Check for the start of the data section
#             if line.strip() == "# DATA":
#                 data_section = True
#                 continue  # Skip the # DATA line

#             # Process lines only after the data section has started
#             if data_section:
#                 # Split the line into components by the delimiter
#                 components = line.strip().split(';')

#                 # Ensure we have the expected number of components (3)
#                 if len(components) == 3:
#                     date = components[0]
#                     value = components[2].strip()

#                     # Write the date and value to the output file
#                     outfile.write(f"{date}    {value}\n")
#.......................................................................................................................................


# code to filter all data from a folder and store output in another directory.......................................
import os
import glob

# Define the input and output directories
input_folder = 'station_data'
output_folder = 'station_data_filtered'

# Create the output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Get a list of all .txt files in the input folder
input_files = glob.glob(os.path.join(input_folder, '*.txt'))

# Process each file
for input_file in input_files:
    # Get the base name of the file (e.g., '1159300_Q_Day.Cmd.txt')
    base_name = os.path.basename(input_file)
    
    # Define the corresponding output file path
    output_file = os.path.join(output_folder, base_name)
    
    # Open the input file for reading with latin-1 encoding
    with open(input_file, 'r', encoding='latin-1') as infile:
        # Open the output file for writing
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Read the file line by line
            data_section = False
            for line in infile:
                # Check for the start of the data section
                if line.strip() == "# DATA":
                    data_section = True
                    continue  # Skip the # DATA line

                # Process lines only after the data section has started
                if data_section:
                    # Split the line into components by the delimiter
                    components = line.strip().split(';')

                    # Ensure we have the expected number of components (3)
                    if len(components) == 3:
                        date = components[0]
                        value = components[2].strip()

                        # Write the date and value to the output file
                        outfile.write(f"{date}    {value}\n")

print("Processing complete. Filtered files saved in 'station_data_filtered' folder.")
#..........................................................................................................................................................