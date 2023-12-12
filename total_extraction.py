from fuzzywuzzy import fuzz
import cv2
from difflib import SequenceMatcher


# Function to calculate similarity ratio between two strings using SequenceMatcher
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

image_path = "/Users/sivagar/Documents/work_projects/general_ocr/key_value/IP1167041 CARMONA HOSPITAL & MEDICAL CENTER INC (p7) (1page)_page-0007.jpg"
image = cv2.imread(image_path)


document_height, document_width, _ = image.shape  # Get the dimensions of the input image

threshold = 0.006*document_height

# Function to extract key-value pairs from OCR results
def extract_key_value(ocr_results, key_name, line_param, value_index, threshold):
    mid_height_results = []

    # Extract middle height of each text bounding box and store in mid_height_results
    for coordinates, (text, _) in ocr_results:
        mid_height = (coordinates[0][1] + coordinates[3][1]) / 2
        mid_height_results.append(((coordinates[0], coordinates[3]), (text, _), mid_height))
    
    
    # sorted results = [(([582.0, 62.0], [582.0, 79.0]), ('MOOCAL.CENTER', 0.7450314164161682), 70.5),....]  (format)

    sorted_results = mid_height_results

    #print(sorted_results)
    
    # Find a key with a high similarity ratio to the specified key_name
    key_match = None
    for (_, _), (text, _), mid_height in sorted_results:
        if similar(key_name.lower(), text.lower()) >= 0.9:
            key_match = text
            break
    
    if key_match is None:
        return None

    #print(key_match)

    # Find the middle height of the matching key
    key_mid_height = None
    for (_, _), (text, _), mid_height in sorted_results:
        if text == key_match:
            key_mid_height = mid_height
            break
    
    if key_mid_height is None:
        return None
    
    # Define height range for extracting values in the same line or next line
    max_next_line_height = key_mid_height + 4*threshold
    threshold2 = key_mid_height + threshold
    values = []


    # Extract values based on line_param ('same_line' or 'next_line')
    for (coordinates[0], coordinates[3]), (text, _), mid_height in sorted_results:
        if line_param == 'same_line' and abs(mid_height - key_mid_height) <= threshold:
            values.append(((coordinates[0], coordinates[3]),text))

        elif line_param == 'next_line' and threshold2 < mid_height <= max_next_line_height:
            values.append(((coordinates[0], coordinates[3]),text))

    #print(values)

    # Sort the extracted values by their x-coordinates
    sorted_strings = sorted(values, key=lambda x: x[0][0][0])
    result_strings = [item[1] for item in sorted_strings]

    #print(result_strings)

    # Return the desired value based on value_index if it exists, otherwise, return None
    if key_match in result_strings:
        i = result_strings.index(key_match)
        if 0 <= value_index < len(result_strings):
            return result_strings[i+value_index]
    else:
        
        if 0 <= value_index < len(result_strings):
                return result_strings[value_index]
        else:
            return None


#example_usage
key_name = "total>>>"
value_in = "same_line"
value_at = 3

result = extract_key_value(total1, key_name, value_in, value_at,threshold)
print(result)