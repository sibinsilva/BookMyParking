import datetime
import logging
import time
import schedule
from email_utils import send_email
from utils import book_spot, initialize_driver, login, target_dates, is_debug


def schedule_booking(target_dates_list):
    """
    Schedules the booking process for the specified target dates.

    Args:
        target_dates_list: A list of target dates in YYYY-MM-DD format.
    """
    next_day = datetime.datetime.now() + datetime.timedelta(days=1)
    for target_date in target_dates_list:
        target_date_obj = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        if target_date_obj == next_day.date():
            driver = initialize_driver()
            if login(driver):
                result, status, spot_number = book_spot(driver, target_date_obj)
                if result == "success":
                    # Format the date as dd/MM/yyyy
                    formatted_date = target_date_obj.strftime("%d/%m/%Y")
                    logging.info("Booking successfully %s for %s - Spot number: %s", status, formatted_date, spot_number)
                    send_email(f"Booking successfully {status} for {formatted_date} - Spot number: {spot_number}")
                else:
                    # Format the date as dd/MM/yyyy
                    formatted_date = target_date_obj.strftime("%d/%m/%Y")
                    logging.warning("Booking failed for %s - Reason: %s", formatted_date, status)
                    send_email(f"Booking failed for {formatted_date} - Reason: {status}")
            else:
                # Format the date as dd/MM/yyyy
                formatted_date = target_date_obj.strftime("%d/%m/%Y")
                logging.warning("Login failed for %s", formatted_date)
                send_email(f"Login failed for {formatted_date}")

if __name__ == "__main__":
    if is_debug: #Run without a schedule on debug mode
        schedule_booking(target_dates.split(','))
    else:
        # Start 5 minutes early to be ready for booking
        schedule.every().day.at("17:55").do(schedule_booking, target_dates_list=target_dates.split(','))

        # Run scheduler continuously
        while True:
            schedule.run_pending()
            time.sleep(1)
