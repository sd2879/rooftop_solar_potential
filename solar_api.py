import cv2
import pytesseract
import re
from geopy import Point
from datetime import datetime, timedelta
import requests

def process_image_with_ocr(image_path, x, y, width, height, output_path="ocr_cropped.png"):
    try:
        # Set the path for Tesseract executable if it's not in your PATH
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust this path if necessary

        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Image not found or unable to read: {image_path}")

        # Convert to grayscale and crop
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop_image = gray_image[y:y + height, x:x + width]
        cv2.imwrite(output_path, crop_image)

        # Perform OCR using PyTesseract
        raw_text = pytesseract.image_to_string(crop_image)

        # Filter text to keep only alphanumeric and specific characters
        filtered_text = re.sub(r'[^0-9a-zA-Z°"\' ]', '', raw_text)

        # Extract scale
        scale_match = re.search(r'\b(\d+(\.\d+)?)\s*[mM]?\b', filtered_text)
        scale = scale_match.group(1) if scale_match else "NA"  # Group 1 captures the numeric part

        # Extract location
        location_match = re.search(r"(\d+°\d+'?\d+\"?[NS])\s+(\d+°\d+'?\d+\"?[EW])", filtered_text)
        location = location_match.group() if location_match else "NA"

    except Exception as e:
        # Set default values and print error message
        print(f"An error occurred: {e}")
        scale = "NA"
        location = "NA"

    return scale, location

def get_lat_long_from_location(location):
    # Add a space after each letter (N, S, E, W) for proper parsing if the location is not "NA"
    location_with_spaces = re.sub(r"([a-zA-Z])", r"\1 ", location) if location != "NA" else "NA"
    
    if location_with_spaces == "NA":
        return "NA", "NA"
    
    try:
        # Use geopy's Point to convert the location string to latitude and longitude
        point = Point(location_with_spaces)
        latitude = float(round(point.latitude, 4))
        longitude = float(round(point.longitude, 4))
        return latitude, longitude
    except Exception as e:
        print(f"Error processing location '{location}': {e}")
        return "NA", "NA"

def fetch_solar_irradiance(latitude, longitude):
    if latitude == "NA" or longitude == "NA":
        return "NA", "NA"
    
    # Get the current date and one year ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Format the dates as YYYYMMDD
    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")

    # Set up the base URL and parameters for the NASA API
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date_str,
        "end": end_date_str,
        "format": "JSON"
    }

    # Make the request to the NASA API
    response = requests.get(base_url, params=params)
    response_data = response.json()

    # Extract irradiance data from the response
    irradiance_data = response_data['properties']['parameter']['ALLSKY_SFC_SW_DWN']

    # Filter out invalid irradiance values (-999.0)
    valid_irradiance_values = [value for value in irradiance_data.values() if value != -999.0]

    # Calculate average and total irradiance
    average_irradiance = sum(valid_irradiance_values) / len(valid_irradiance_values)
    total_irradiance = sum(valid_irradiance_values)

    return round(average_irradiance, 2), round(total_irradiance, 2)

# Main function to orchestrate the whole process
def solar_info(image_path, x= 788, y= 605, width=2000, height=200):
    # Step 1: Process the image and extract the scale and location
    scale, location = process_image_with_ocr(image_path, x, y, width, height)
    print(f"Extracted Scale: {scale}")
    print(f"Extracted Location: {location}")

    # Step 2: Convert the extracted location into latitude and longitude
    latitude, longitude = get_lat_long_from_location(location)
    print(f"Latitude: {latitude}, Longitude: {longitude}")

    # Step 3: Fetch solar irradiance data based on the extracted coordinates
    if latitude != "NA" and longitude != "NA":
        average_irradiance, total_irradiance = fetch_solar_irradiance(latitude, longitude)
        print(f"Average Irradiance: {average_irradiance} kWh/m²/day")
        print(f"Total Irradiance: {total_irradiance} kWh/m²/year")
    else:
        print("Invalid location for irradiance data.")
    
    return scale, location, average_irradiance, total_irradiance

