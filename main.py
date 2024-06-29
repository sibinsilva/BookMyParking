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
import schedule
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
receiver_email = os.getenv("RECEIVER_EMAIL")
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))

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
                gritter_text = gritter_wrapper.text
                #send email to do manually
                print("Gritter notice wrapper found.")
                send_email("This is a fail test email sent from BookMyParking. " + "/n Reason: " + gritter_text + "/n")
            else:
                print("Gritter notice wrapper not found.")
                send_email("This is a pass test email sent from BookMyParking.")
        except:
            #send email to do manually
            print("Gritter notice wrapper not found or timeout occurred.")
            send_email("An exception occured in BookMyParking.")
        time.sleep(300) 
        driver.quit()
        return True
    except Exception as e:
        logging.error(f"Booking failed: {e}")
        return False

def schedule_booking(target_dates):
    next_day = datetime.datetime.now() + datetime.timedelta(days=1)
    target_dates = target_dates.split(',')
    for target_date in target_dates:
        target_date = target_date.strip()
        target_date_obj = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        if target_date_obj == next_day.date():
            driver = initialize_driver()
            if login(driver):
                if book_spot(driver, target_date_obj):
                    logging.info(f"Booking successful for {target_date_obj}")
                    send_email(f"Booking successful for {target_date_obj}")
                else:
                    logging.warning(f"Booking failed for {target_date_obj}")
                    send_email(f"Booking failed for {target_date_obj}")
            else:
                logging.warning(f"Login failed for {target_date_obj}")
                send_email(f"Login failed for {target_date_obj}")

def send_email(body):
    # Create the container email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = 'Test Email from BookMyParking'

    # Attach the body of the email to the MIME message
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the SMTP server and secure the connection
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    if is_debug: #Run without a schedule on debug mode
        schedule_booking(target_dates)
    else:
        # Start 5 minutes early to be ready for booking
        schedule.every().day.at("17:55").do(schedule_booking, target_dates=target_dates)

        # Run scheduler continuously
        while True:
            schedule.run_pending()
            time.sleep(1)
