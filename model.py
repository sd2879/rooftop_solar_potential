import numpy as np
import cv2
import os
from ultralytics import YOLO
import torch

def process_image(image_path: str, output_path: str = 'output.png', conf: float = 0.80, iou: float = 0.80) -> str:
    """
    Process an image using YOLO model for object detection and segmentation, and save the result with overlays.
    
    Parameters:
        image_path (str): Path to the input image.
        output_path (str): Path where the processed image will be saved.
        conf (float): Confidence threshold for YOLO model.
        iou (float): IOU threshold for YOLO model.

    Returns:
        str: Path to the saved output image.
    """
    
    # Initialize YOLO model
    yolo_model = YOLO('rooftop_model.pt')

    # Load image using OpenCV
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Image not found at the path: {image_path}")

    # Convert the image from BGR (OpenCV format) to RGB (Matplotlib format)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Run YOLO model on the image (with segmentation enabled)
    results = yolo_model(image, conf=conf, iou=iou)

    # Get segmentation masks and bounding boxes (if available in the results)
    masks = results[0].masks
    boxes = results[0].boxes

    # Create a copy of the original image for drawing
    final_image = image_rgb.copy()

    if masks:
        mask_image = np.zeros_like(image_rgb)
        
        # Loop through each mask and apply it to the image
        for idx, mask in enumerate(masks.data):
            # Convert mask from float to 8-bit and resize to match the image dimensions
            mask_resized = cv2.resize(mask.cpu().numpy().astype(np.uint8) * 255, (image_rgb.shape[1], image_rgb.shape[0]))
            
            # Colorize the mask (here, we use red)
            mask_colored = np.zeros_like(image_rgb)
            mask_colored[mask_resized == 255] = [255, 0, 0]  # Color the mask red
            
            # Overlay the colored mask onto the original image
            mask_image = cv2.addWeighted(mask_image, 1.0, mask_colored, 0.5, 0)
        
        # Combine the original image with the mask image
        final_image = cv2.addWeighted(image_rgb, 1.0, mask_image, 0.5, 0)
    
    # Draw bounding boxes and labels
    if boxes:
        for i, box in enumerate(boxes.xyxy):  # Assuming `boxes.xyxy` contains bounding box coordinates
            x1, y1, x2, y2 = map(int, box)
            # cv2.rectangle(final_image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw bounding box in green
            
            # Calculate centroid
            centroid_x = (x1 + x2) // 2
            centroid_y = (y1 + y2) // 2

            # Define font scale
            font_scale = 0.5
            thickness = 2
            
            # Draw the object number
            cv2.putText(final_image, str(i + 1), (centroid_x, centroid_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
    
    # Save the image with segmentation masks and labels
    center_x = 269
    center_y = 235
    radius = 5
    color = (0, 0, 0)
    thickness = -1
    cv2.circle(final_image, (center_x, center_y), radius, color, thickness)
    cv2.imwrite(output_path, cv2.cvtColor(final_image, cv2.COLOR_RGB2BGR))
    
    return results

def analyze_masks(results, total_area: float, center_x: int = 270, center_y: int = 235, size_of_point: int = 20, mask_threshold: float = 0.5):
    """
    Analyze segmentation masks, calculate percentage areas, and determine masks within a given ROI.

    Parameters:
        results: The result object from YOLO model containing masks and bounding boxes.
        total_area (float): Total area of the region for calculating the actual rooftop areas.
        center_x (int): X-coordinate of the center point for ROI.
        center_y (int): Y-coordinate of the center point for ROI.
        size_of_point (int): Size of the ROI for selecting rooftops. Increased default size for larger region check.
        mask_threshold (float): Threshold to binarize masks. Default is 0.5.
    
    Returns:
        dict: A dictionary containing all mask areas and the mask within the defined ROI.
    """
    
    # Extract masks from YOLO results
    masks = results[0].masks
    if masks is None:
        raise ValueError("No masks found in the results.")

    mask_data = masks.data  # Assuming masks.data is a tensor or numpy array (C, H, W)
    
    # Get total pixels for percentage calculation
    total_pixels = mask_data.shape[1] * mask_data.shape[2]
    print(f"Total Pixels: {total_pixels}")
    
    # Calculate the area of each mask and percentage relative to the total image
    mask_dict = {}
    mask_areas = [mask.sum().item() for mask in mask_data]
    mask_percentages = [(area / total_pixels) * 100 for area in mask_areas]

    # Output all rooftop areas
    print("######################################################################################")
    print("All rooftops")
    for i, (percentage, area) in enumerate(zip(mask_percentages, mask_areas)):
        mask_number = i + 1
        pixel_area = area
        percent_area = round(percentage, 2)
        actual_area = round(((percentage * total_area) / 100), 2)
        mask_dict[mask_number] = actual_area

        print(f"Mask: {mask_number}, Pixel Area: {pixel_area}, Percent Area: {percent_area:.2f}%, Actual Area: {actual_area}")
    
    # Dictionary to store all data
    mask_analysis = {"all_mask_area": mask_dict}

    # Now check if the point (center_x, center_y) falls within any mask, considering the size_of_point
    roi_mask_found = False
    print("######################################################################################")
    print(f"Checking if region around point ({center_x}, {center_y}) falls within any mask...")

    for i, mask in enumerate(mask_data):
        # Apply a threshold to the mask to ensure it's binary
        mask_bool = mask > mask_threshold

        # Define a larger region to increase chances of detection
        x_min = max(0, center_x - size_of_point)
        x_max = min(mask_data.shape[2], center_x + size_of_point + 1)
        y_min = max(0, center_y - size_of_point)
        y_max = min(mask_data.shape[1], center_y + size_of_point + 1)

        # Convert mask to boolean and check if any value is inside the mask
        region_bool = mask_bool[y_min:y_max, x_min:x_max]
        print(f"Checking mask {i+1}: Region {region_bool.shape} with bounds x:({x_min},{x_max}), y:({y_min},{y_max})")

        if region_bool.sum().item() > 0:
            print(f"Region around point ({center_x}, {center_y}) falls within mask {i+1}.")
            roi_mask_found = True
            
            # Update mask_analysis with target mask info
            percent_area = mask_percentages[i]
            actual_area = round(((percent_area * total_area) / 100), 2)
            mask_analysis["target_mask"] = {i + 1: actual_area}
            break
    
    if not roi_mask_found:
        print(f"Region around point ({center_x}, {center_y}) does not fall within any mask.")
        mask_analysis["target_mask"] = None
    
    return mask_analysis


