import os, csv
import numpy as np
import warnings
from visualization import generate_combined_barcode
warnings.filterwarnings("ignore")

headers = [
        'Filepath', 'Channel', 'Flags', 'Connectivity', 'Maximum Island Area', 'Maximum Void Area', 
        'Island Area Change', 'Void Area Change', 'Initial Maximum Island Area', 
        'Initial 2nd Maximum Island Area', 'Maximum Kurtosis', 'Maximum Median Skewness', 
        'Maximum Mode Skewness', 'Kurtosis Change', 'Median Skewness Change', 
        'Mode Skewness Change', 'Mean Speed', 'Speed Change',
        'Mean Flow Direction', 'Flow Directional Spread']

def write_file(output_filepath, data):
    global headers
    if data:
        with open(output_filepath, 'w', newline='', encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(headers) # Write headers before the first filename
            headers = [] # Ensures headers are only written once per file
            for entry in data:
                csvwriter.writerow(entry)

def generate_aggregate_csv(csv_list, csv_loc, gen_barcode, sort = None, separate_channel = False):
    global headers
    if gen_barcode:
        combined_barcode_loc = os.path.join(os.path.dirname(csv_loc), f'{os.path.basename(csv_loc).removesuffix('.csv')} Barcode')
        
    num_params = len(headers) - 1
    csv_data = np.zeros(shape=(num_params))
    if not csv_list:
        return None
    if len(csv_list) == 1 and csv_list[0] == csv_loc:
        with open(csv_loc, 'r', newline='\n') as fread:
                csv_reader = csv.reader(fread)
                next(csv_reader, None)
                for row in csv_reader:
                    row = [float(val) if val != '' else np.nan for val in row[1:]]
                    arr_row = np.array(row)
                    csv_data = np.vstack((csv_data, arr_row))
    else:
        with open(csv_loc, 'w', encoding="utf-8", newline="\n") as fwrite:
            csv_writer = csv.writer(fwrite)
            csv_writer.writerow(headers)
            for csv_file in csv_list:
                with open(csv_file, 'r', newline='\n') as fread:
                    csv_reader = csv.reader(fread)
                    next(csv_reader, None)
                    for row in csv_reader:
                        csv_writer.writerow(row)
                        row = [float(val) if val != '' else np.nan for val in row[1:]]
                        arr_row = np.array(row)
                        csv_data = np.vstack((csv_data, arr_row))

    csv_data = csv_data[1:]

    if gen_barcode:
        generate_combined_barcode(csv_data, combined_barcode_loc, sort, separate_channel)
