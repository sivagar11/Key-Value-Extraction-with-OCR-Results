from typing import List, Tuple, Dict, Union
import json


def calculate_confidence_score(
    key_coordinate: List[List[float]],
    value_coordinate: List[List[float]],
    value_confidence: float,
    horizontal_threshold: float,
    vertical_threshold: float,
) -> float:
    """
    Calculates the confidence score for a key-value pair.

    :param key_coordinate: Coordinate of the key (list of points [[x1, y1], [x2, y2], ...]).
    :param value_coordinate: Coordinate of the value (list of points [[x1, y1], [x2, y2], ...]).
    :param value_confidence: OCR confidence score of the value.
    :param horizontal_threshold: Threshold for horizontal distance to consider key and value on the same line.
    :param vertical_threshold: Threshold for vertical distance to consider key and value on the same line.
    :return: Confidence score (0 to 1).
    """
    # Load coefficients and intercept from config file
    with open("key_value_confidence_score_config.json", "r") as config_file:
        config = json.load(config_file)
        value_confidence_coefficient = config["value_confidence_coefficient"]
        vertical_distance_coefficient = config["vertical_distance_coefficient"]
        horizontal_distance_coefficient = config["horizontal_distance_coefficient"]
        intercept = config["intercept"]

    # Calculate the horizontal and vertical distance between key and value
    horizontal_distance = abs(value_coordinate[1][0] - key_coordinate[1][0])
    vertical_distance = abs(value_coordinate[0][1] - key_coordinate[0][1])

    # Check if key and value are on the same line
    vertical_distance_factor = max(0, 1 - (vertical_distance / vertical_threshold))

    # Distance factor (normalized to be between 0 and 1)
    # Assuming that a larger distance reduces confidence
    horizontal_distance_factor = max(
        0, 1 - (horizontal_distance / (2 * horizontal_threshold))
    )

    # Combine factors
    combined_confidence = (
        (value_confidence_coefficient * value_confidence)
        + (vertical_distance_coefficient * vertical_distance_factor)
        + (horizontal_distance_coefficient * horizontal_distance_factor)
        + intercept
    )

    return combined_confidence


def calculate_average_confidence(confidence_scores: Dict[str, float]) -> float:
    """
    Calculates the average confidence score for all key-value pairs.

    :param confidence_scores: Dictionary containing confidence scores for key-value pairs.
    :return: Average confidence score.
    """
    if not confidence_scores:
        return 0.0

    total_confidence = sum(confidence_scores.values())
    average_confidence = total_confidence / len(confidence_scores)
    return average_confidence


def extract_key_value(
    ocr_results: List[Tuple[List[List[float]], Tuple[str, float]]],
    expected_keys: List[List[str]],
    horizontal_threshold: float,
    vertical_threshold: float,
) -> Dict[str, Union[str, Tuple[str, float]]]:
    extracted_data = {}
    used_indices = set()
    key_value_confidences = {}  # Store confidence scores for each key-value pair
    key_coordinates_list = []

    # Step 1: Identify Keys and Extract Values
    for key_group in expected_keys:
        for key_variant in key_group:
            for idx, ocr_result in enumerate(ocr_results):
                if idx not in used_indices:
                    ocr_text, confidence = ocr_result[1]
                    if fuzz.partial_ratio(key_variant.lower(), ocr_text.lower()) > 90:
                        key_text = ocr_text
                        key_coordinates = ocr_result[0]
                        if ":" in key_text and key_text.index(":") < len(key_text) - 1:
                            key_name, value_text = map(
                                str.strip, key_text.split(":", 1)
                            )
                            # Assign a higher confidence for key-value pairs in the same bounding box
                            higher_confidence = 0.85 + (0.1 * confidence)
                            extracted_data[key_variant] = (
                                value_text,
                                min(higher_confidence, 1),
                            )  # Ensuring max confidence is 1
                        else:
                            key_coordinates_list.append([key_variant, key_coordinates])
                        used_indices.add(idx)

    # Step 2: Assign Values Based on Coordinates and Calculate Confidence Scores
    for key, key_coordinate in key_coordinates_list:
        value_text = ""  # Initialize an empty string to store the extracted value text
        value_confidence = (
            0  # Initialize a variable to store the OCR confidence of the value
        )
        value_coordinate = (
            None  # Initialize a variable to store the coordinates of the value
        )
        for idx, ocr_result in enumerate(ocr_results):
            if idx not in used_indices:
                text_coordinates = ocr_result[0]
                text = ocr_result[1][0].strip()
                text_confidence = ocr_result[1][1]  # OCR confidence score of the text
                if (
                    abs(text_coordinates[0][1] - key_coordinate[0][1])
                    <= vertical_threshold
                    and key_coordinate[1][0] - horizontal_threshold
                    <= text_coordinates[0][0]
                    <= key_coordinate[1][0] + 2 * horizontal_threshold
                ):
                    value_text += text + " "
                    value_confidence = round(text_confidence, 4)
                    value_coordinate = text_coordinates
                    used_indices.add(idx)
                    extracted_data[key] = value_text.strip()
                    break
        if value_coordinate:
            key_value_confidence = calculate_confidence_score(
                key_coordinate,
                value_coordinate,
                value_confidence,
                horizontal_threshold,
                vertical_threshold,
            )
            extracted_data[key] = (value_text.strip(), key_value_confidence)
            key_value_confidences[
                key
            ] = key_value_confidence  # Store confidence score for the key-value pair

    # Calculate average confidence score
    average_confidence = calculate_average_confidence(key_value_confidences)

    return (
        extracted_data,
        average_confidence,
    )  # Return the final extracted data dictionary and confidence scores
