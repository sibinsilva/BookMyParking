import datetime
import time
import random
import os
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(filename='booking_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Get the URL, email, and password from the environment variables
url = os.getenv('URL')
email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')
target_dates = os.getenv('TARGET_DATES')
is_debug = os.getenv('IS_DEBUG')

def initialize_driver():
    options = webdriver.ChromeOptions()
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def slow_type(element, text, delay=0.1):
    for char in text:
        element.send_keys(char)
        time.sleep(delay)

def login(driver):
    driver.get(url)
    driver.maximize_window()
    try:
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'email')))
        slow_type(email_input, email)
        time.sleep(random.uniform(0.5, 2.0))
        terms_checkbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="empRegCheckBox"]')))
        driver.execute_script("arguments[0].click();", terms_checkbox)
        time.sleep(random.uniform(0.5, 2.0))
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'emailConfirmButton')))
        driver.execute_script("arguments[0].scrollIntoView();", confirm_button)
        confirm_button.click()
        next_page_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'manual_5')))
        driver.execute_script("arguments[0].scrollIntoView();", next_page_element)
        time.sleep(random.uniform(0.5, 2.0))
        next_page_element.click()
        return True
    except Exception as e:
        logging.error(f"Login failed: {e}")
        return False

def book_spot(driver, target_date):
    try:
        password_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'password')))
        slow_type(password_input, password)
        time.sleep(random.uniform(0.5, 2.0))
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'loginBtn')))
        driver.execute_script("arguments[0].scrollIntoView();", login_button)
        login_button.click()
        time.sleep(10) 

        now = datetime.datetime.now()
        target_time = datetime.datetime(now.year, now.month, now.day, 18, 0)  # 6 PM today
        time_remaining = (target_time - now).total_seconds()

        # Wait until 6 PM
        if not is_debug:
            if time_remaining > 0:
                print(f"Waiting for {time_remaining} seconds until 6 PM...")
                time.sleep(time_remaining)

        date_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, f'//a[@id="{target_date}"]')))
        day_of_week = target_date.strftime('%a')
        try:
            circle_element = date_element.find_element(By.CLASS_NAME, 'fa-circle')
            circle_element.click()
            modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "myModal")))
            button = modal.find_element(By.ID, "claim_SpotID")
            button.click()
        except: # If parking is already alloted, release it.
            spot_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f'a.SpotID_assigned.day_{day_of_week}.VehicleTypeId_0'))
            )
            spot_element.click()
            modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "release_modal")))
            button = modal.find_element(By.ID, "release_SpotID")
            button.click()
        
        # Wait for the presence of the gritter notice wrapper
        try:
            gritter_wrapper = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "gritter-notice-wrapper"))
            )
            # If the gritter wrapper is found, you can perform further actions here
            if gritter_wrapper:
                gritter_text = gritter_wrapper.text
                #This means that it could be either success/failure. Read Gritter notice to get the actual message
                if gritter_text.startswith("SUCCESS"):
                    if "Assigned" in gritter_text: #Claim spot
                        return "success", "claimed", gritter_text.split()[1]
                    else: #Release spot
                        return "success", "released", gritter_text.split()[2]
                else: #failed due to some reason
                    return "failure", gritter_text, ""
            else:
                logging.debug("Gritter notice wrapper not found.")
                return "failure", "Gritter notice wrapper not found."
        except:
            #send email to do manually
            logging.debug("Gritter notice wrapper not found or timeout occurred.")
            return "failure", "Gritter notice wrapper not found or timeout occurred."
        time.sleep(300) 
        driver.quit()
    except Exception as e:
        logging.error(f"Booking failed: {e}")
        return False
