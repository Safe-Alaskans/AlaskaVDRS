import json
import os

def filter_and_save_json(input_file):
    # Load and parse the JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Filter and modify the data
    filtered_data = [item for item in data if item.get('rank', 0) > 40]
    for item in filtered_data:
        del item['rank']

    # Create new filename
    dir_path = os.path.dirname(input_file)
    file_name = os.path.basename(input_file)
    new_file_name = f"top60pct_pairs_{file_name}"
    output_file = os.path.join(dir_path, new_file_name)

    # Save modified data to new file, preserving original formatting
    with open(output_file, 'w') as f:
        json.dump(filtered_data, f, indent=4)

    print(f"Filtered data saved to: {output_file}")
    return output_file

# Prompt user for input file
input_file = input("Enter the path to the input JSON file: ")

# Run the filter and save function
try:
    output_file = filter_and_save_json(input_file)
    print(f"\nScript executed successfully!")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
except Exception as e:
    print(f"\nAn error occurred: {str(e)}")
