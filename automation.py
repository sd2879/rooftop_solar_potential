import os
import cv2
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from config import get_paths
from model import process_image, analyze_masks
from solar_api import solar_info
import json

class GoogleEarthAutomation:
    def __init__(self, timestamp, place_name):
        self.paths = get_paths(timestamp)
        self.place_name = place_name
        self.options = FirefoxOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--headless')

        # Set up WebDriver
        self.driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=self.options)
        self.action_chains = ActionChains(self.driver)

        # Open Google Earth and set window size after it loads
        self.driver.get("https://earth.google.com/")
        time.sleep(2)
        self.driver.set_window_size(1280, 720)
        time.sleep(5)
        print(f"Current window size: {self.driver.get_window_size()}")
        # self.driver.save_screenshot(os.path.join(self.paths['run_screenshot'], '1_load_page.png'))

    def resize_image(self, input_path, output_path, size):
        """Resize image to the specified size using OpenCV."""
        image = cv2.imread(input_path)
        image_resized = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
        cv2.imwrite(output_path, image_resized)

    def measure_time(self, func, *args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result
    
    def send_keys_with_action_chains(self, driver, key1, key2):
        action = ActionChains(driver)
        action.key_down(key1).key_down(key2).key_up(key2).key_up(key1).perform()

    def configure_layers(self):
        try:
            self.driver.find_element(By.XPATH, "//*").send_keys(Keys.ESCAPE)
            time.sleep(2)
            # self.driver.save_screenshot(os.path.join(self.paths['run_screenshot'], '2_click_esc.png'))
            self.send_keys_with_action_chains(self.driver, Keys.CONTROL, 'b')
            time.sleep(2)
            # self.driver.save_screenshot(os.path.join(self.paths['run_screenshot'], '3_click_layers.png'))
            self.action_chains.move_by_offset(245, 277).click().perform()
            time.sleep(2)
            # self.driver.save_screenshot(os.path.join(self.paths['run_screenshot'], '4_click_layers_clean.png'))
            self.send_keys_with_action_chains(self.driver, Keys.CONTROL, 'b')
            time.sleep(2)
            self.driver.find_element(By.TAG_NAME, "body").send_keys('/')
            time.sleep(2)
            # self.driver.save_screenshot(os.path.join(self.paths['run_screenshot'], '5_click_search.png'))
        except Exception as e:
            print(f"Error configuring layers: {e}")

    def search_place(self):
        try:
            search_field = self.driver.find_element(By.TAG_NAME, "body")
            time.sleep(1)
            search_field.send_keys(Keys.CONTROL + 'a')
            time.sleep(1)
            search_field.send_keys(Keys.BACKSPACE)
            time.sleep(1)
            search_field.send_keys(self.place_name)
            time.sleep(2)
            search_field.send_keys(Keys.ENTER)
            time.sleep(20)
            screenshot_path_marker = os.path.join(self.paths['place_screenshot_marker'], self.place_name + '.png')
            self.driver.save_screenshot(screenshot_path_marker)
            time.sleep(1)
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(2)
            screenshot_path = os.path.join(self.paths['place_screenshot'], self.place_name + '.png')
            self.driver.save_screenshot(screenshot_path)
        except Exception as e:
            print(f"Error searching place: {e}")

    def process_screenshots(self, input_folder_path, output_folder_path, cropped_folder_path):
        images = os.listdir(input_folder_path)
        for img_name in images:
            img_input_path = os.path.join(input_folder_path, img_name)
            img_output_path = os.path.join(output_folder_path, img_name)
            img_cropped_path = os.path.join(cropped_folder_path, img_name)
            image = cv2.imread(img_input_path)
            if image is not None:
                h, w = image.shape[:2]
                rect_width = 540
                rect_height = 470
                x_center = 640
                y_center = 315
                x = x_center - (rect_width // 2)
                y = y_center - (rect_height // 2)
                rect_bottom_right_x = x + rect_width
                rect_bottom_right_y = y + rect_height
                cv2.rectangle(image, (x, y), (rect_bottom_right_x, rect_bottom_right_y), (0, 255, 0), 2)
                cv2.imwrite(img_output_path, image)
                crop_image = image[y:rect_bottom_right_y, x:rect_bottom_right_x]
                cv2.imwrite(img_cropped_path, crop_image)
            else:
                print(f"Error reading image: {img_name}")


    def process_satellite_images(self):
        img_input_path = os.path.join(self.paths['satellite_images'], self.place_name + '.png')
        img_output_path = os.path.join(self.paths['yolo_output'], self.place_name + '.png')
        
        try:
            results = process_image(img_input_path, img_output_path)
            total_area = 36000
            mask_analysis = analyze_masks(results, total_area)
            print(f"Target Mask: {mask_analysis}")
        except Exception as e:
            mask_analysis = {}
            print(f"Error processing image {self.place_name + '.png'}: {e}")
        
        return json.dumps(mask_analysis)

    
    def ocr_solar_info(self):
        img_input_path = os.path.join(self.paths['place_screenshot'], self.place_name + '.png')
        scale, location, average_irradiance, total_irradiance = solar_info(img_input_path)
        return scale, location, average_irradiance, total_irradiance

    def process(self):
        self.measure_time(self.configure_layers)
        self.measure_time(self.search_place)
        self.measure_time(self.process_screenshots, self.paths['place_screenshot_marker'], self.paths['place_screenshot_marker'], self.paths['satellite_images_marker'])
        self.measure_time(self.process_screenshots, self.paths['place_screenshot'], self.paths['place_screenshot'], self.paths['satellite_images'])
        self.measure_time(self.process_satellite_images)
        self.measure_time(self.ocr_solar_info)
        
    def close(self):
        self.driver.quit()

# timestamp = '20240914'
# place_name = 'Sir Duncan Rice Library, Aberdeen'

# automation = GoogleEarthAutomation(timestamp, place_name)
# automation.process()
# automation.close()
