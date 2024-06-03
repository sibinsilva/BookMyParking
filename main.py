import datetime
import time
import random
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import schedule

# Load environment variables from .env file
load_dotenv()

# Get the URL, email, and password from the environment variables
url = os.getenv('URL')
email = os.getenv('EMAIL')
password = os.getenv('PASSWORD')
target_dates = os.getenv('TARGET_DATES')

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

def book_spot(driver, target_date):
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
    if time_remaining > 0:
        print(f"Waiting for {time_remaining} seconds until 6 PM...")
        time.sleep(time_remaining)

    date_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, f'//a[@id="{target_date}"]')))
    circle_element = date_element.find_element(By.CLASS_NAME, 'fa-circle')
    circle_element.click()
    modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "myModal")))
    button = modal.find_element(By.ID, "claim_SpotID")
    button.click()
    # Wait for the presence of the gritter notice wrapper
    try:
        gritter_wrapper = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gritter-notice-wrapper"))
        )
        # If the gritter wrapper is found, you can perform further actions here
        if gritter_wrapper:
            #send email to do manually
            print("Gritter notice wrapper found.")
        else:
            #A retry maybe required
            print("Gritter notice wrapper not found.")
    except:
        #send email to do manually
        print("Gritter notice wrapper not found or timeout occurred.")
    time.sleep(300) 
    driver.quit()

def schedule_booking(target_dates):
    next_day = datetime.datetime.now() + datetime.timedelta(days=1)
    target_dates = target_dates.split(',')
    for target_date in target_dates:
        target_date = target_date.strip()
        target_date_obj = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        if target_date_obj == next_day.date():
            driver = initialize_driver()
            login(driver)
            book_spot(driver, target_date_obj)

if __name__ == "__main__":
    # Start 5 minutes early to be ready for booking
    schedule.every().day.at("17:55").do(schedule_booking, target_dates=target_dates)

    # Run scheduler continuously
    while True:
        schedule.run_pending()
        time.sleep(1)
