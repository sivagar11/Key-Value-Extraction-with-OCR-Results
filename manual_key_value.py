from fuzzywuzzy import fuzz
import cv2

image_path = "/content/IP1164996 MARY MEDIATRIX MEDICAL CENTER (p6-7) (2pages)_page-0001.jpg"
image = cv2.imread(image_path)

document_height, document_width, _ = image.shape  # Get the dimensions of the input image
heightthresh=0.009
widththresh=0.075

# Calculate horizontal and vertical thresholds based on the document size
horizontal_threshold = widththresh*document_width
vertical_threshold = heightthresh*document_height

def extract_key_value(ocr_results, expected_keys, horizontal_threshold, vertical_threshold):
    extracted_data = {}  # Dictionary to store extracted key-value pairs
    used_indices = set()  # Set to keep track of used OCR result indices
    key_coordinates_list= []  #[[key,coordinate],[key,coordinate]] (format)
    # Step 1: Identify Keys
    for key_group in expected_keys:
        for key_variant in key_group:
            for idx, ocr_result in enumerate(ocr_results):
                if idx not in used_indices:
                    ocr_text = ocr_result[1][0]  # Extract OCR text from the current result
                    
                    if fuzz.partial_ratio(key_variant.lower(), ocr_text.lower()) > 90:
                        key_text = ocr_results[idx][1][0]  # Extract the key text
                        key_coordinates = ocr_results[idx][0]  # Extract the key coordinates

                        # If key text has a colon, split it into key and value, else store for later processing
                        if ":" in key_text and key_text.index(":") < len(key_text) - 1:
                            key_name, value_text = map(str.strip, key_text.split(":", 1))
                            extracted_data[key_variant] = value_text
                        
                        else:
                            key_coordinates_list.append([key_variant,key_coordinates])

                        used_indices.add(idx)  # Mark the index as used to avoid duplicate processing

    

    # Step 2: Assign Values Based on Coordinates
    for key,key_coordinate in key_coordinates_list:
        
            value_text = ""  # Initialize an empty string to store the extracted value text for the current key
            for idx, ocr_result in enumerate(ocr_results):
                if idx not in used_indices:  # Check if the OCR result at the current index has not been used before
                    text_coordinates = ocr_result[0]  # Extract the coordinates of the current OCR result
                    text = ocr_result[1][0].strip()  # Extract the OCRtext and remove leading and trailing spaces
                    
                    if abs(text_coordinates[0][1] - key_coordinate[0][1]) <= vertical_threshold and \
                      key_coordinate[0][1] - horizontal_threshold <= text_coordinates[0][1] <= key_coordinate[1][1] + horizontal_threshold:
                        value_text += text + " "  # Add the text to the value_text string with a space separator
                        used_indices.add(idx)  # Mark the current OCR result index as used
                        extracted_data[key] = value_text.strip()  
                        break

            

    return extracted_data  # Return the final extracted data dictionary


# Example Usage:
extracted_data = extract_key_value(ocr_results, expected_keys,horizontal_threshold, vertical_threshold)
print(extracted_data)
