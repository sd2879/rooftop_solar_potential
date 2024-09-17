import gradio as gr
import os
import json
from automation import GoogleEarthAutomation

def run_automation(place_name):
    timestamp = '20240914'
    automation = GoogleEarthAutomation(timestamp, place_name)
    automation.process()
    
    # Get paths and results
    image_path = os.path.join(automation.paths['yolo_output'], place_name + '.png')
    scale, location, average_irradiance, total_irradiance = automation.ocr_solar_info()
    target_mask_info = automation.process_satellite_images()
    
    # Close automation
    automation.close()
    
    return (image_path, scale, location, average_irradiance, total_irradiance, target_mask_info)

def gradio_interface(place_name):
    image, scale, location, average_irradiance, total_irradiance, target_mask_info = run_automation(place_name)    
    solar_info = f"Scale: {scale}\nLocation: {location}\nAverage Irradiance: {average_irradiance} W/m^2\nTotal Irradiance: {total_irradiance} kWh/m^2"
    
    # Convert mask analysis dictionary to JSON string
    mask_analysis_info = json.loads(target_mask_info)
    
    return image, solar_info, mask_analysis_info

# Gradio Interface
inputs = gr.Textbox(label="Enter Location", placeholder="Enter the house name, City name.")
outputs = [
    gr.Image(label="Rooftop Image, location the black dot for your rooftop."),
    gr.Textbox(label="Solar Information"),
    gr.JSON(label="Mask Analysis")
]

gr.Interface(
    fn=gradio_interface,
    inputs=inputs,
    outputs=outputs,
    title="Rooftop Solar Potential, POWERED BY AI"
).launch(share=True)
