import sys
import time
import logging
import os
import zipfile
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# Email configuration
EMAIL_ADDRESS = "subhobot2412@gmail.com"
EMAIL_PASSWORD = "wfmt xprw ypuv tfvi"  # Consider using environment variables for better security
RECIPIENT_EMAIL = sys.argv[1] if len(sys.argv) > 1 else "subhobot2000@gmail.com"

# Paths
BASE_FOLDER = "C:\\NSE BOT MAIN\\Downloaded Report"
LOG_FILE = "C:\\NSE BOT MAIN\\NSE_TXT_LOG_ORG.txt"

# Set up logging
if not os.path.exists("C:\\NSE BOT MAIN"):
    os.makedirs("C:\\NSE BOT MAIN")
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8', delay=False),
        logging.StreamHandler()
    ]
)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
)

# Generate dated folder for each run
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_FOLDER = os.path.join(BASE_FOLDER, timestamp)
os.makedirs(RUN_FOLDER, exist_ok=True)
prefs = {"download.default_directory": RUN_FOLDER}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def send_email(subject, body, attachment_path=None):
    """Send an email with optional attachment."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}"
            )
            msg.attach(part)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            logging.info(f"Email sent successfully to {RECIPIENT_EMAIL}.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def rename_file_with_timestamp(folder, file_name):
    """Rename file with timestamp to ensure uniqueness and clarity."""
    base_name, ext = os.path.splitext(file_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{timestamp}_{base_name}{ext}"
    new_path = os.path.join(folder, new_name)

    count = 1
    while os.path.exists(new_path):
        new_name = f"{timestamp}_{base_name}({count}){ext}"
        new_path = os.path.join(folder, new_name)
        count += 1

    old_path = os.path.join(folder, file_name)
    os.rename(old_path, new_path)
    logging.info(f"Renamed file: {file_name} to {new_name}")
    return new_name

def unzip_files(folder):
    """Unzip any ZIP files in the folder and delete the ZIP after extraction."""
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if file_path.endswith(".zip"):
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    extract_path = os.path.join(folder, file_name.replace('.zip', ''))
                    os.makedirs(extract_path, exist_ok=True)
                    zip_ref.extractall(extract_path)
                    logging.info(f"Unzipped file: {file_name}")
                os.remove(file_path)
                logging.info(f"Deleted ZIP file: {file_name}")
            except Exception as e:
                logging.error(f"Failed to unzip {file_name}: {e}")

def organize_files_by_type(folder):
    """Organize files into subfolders based on their type."""
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(file_name)[-1].lower().strip(".")
            type_folder = os.path.join(folder, file_ext.upper())
            os.makedirs(type_folder, exist_ok=True)
            os.rename(file_path, os.path.join(type_folder, file_name))
            logging.info(f"Moved {file_name} to {type_folder}")

def download_file(link, download_path):
    """Download a single file and wait for completion."""
    try:
        initial_files = set(os.listdir(download_path))
        driver.execute_script("arguments[0].scrollIntoView(true);", link)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", link)
        logging.info(f"Clicked on download link: {link.get_attribute('href')}")

        timeout = 60
        while timeout > 0:
            new_files = set(os.listdir(download_path)) - initial_files
            if new_files:
                downloaded_file = new_files.pop()
                if not downloaded_file.endswith(".crdownload"):
                    logging.info(f"Downloaded: {downloaded_file}")
                    return downloaded_file
            time.sleep(1)
            timeout -= 1

        logging.warning("File download timed out.")
        return None
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return None

def main():
    try:
        # Navigate to the target page
        driver.get("https://www.nseindia.com/all-reports")
        logging.info("Navigated to the target page.")

        # Wait for the specific section to load
        section_xpath = "/html/body/div[11]/div[2]/div/section/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[1]/div/div[5]/div"
        WebDriverWait(driver, 40).until(EC.presence_of_element_located(
            (By.XPATH, section_xpath)
        ))
        logging.info("Page loaded and section found successfully.")

        # Locate the section with download icons
        report_section = driver.find_element(By.XPATH, section_xpath)
        download_links = report_section.find_elements(By.XPATH, ".//span/a")

        if not download_links:
            logging.warning("No download links found.")
            return

        logging.info(f"Found {len(download_links)} download links.")
        failed_downloads = []
        for link in download_links:
            file_name = download_file(link, RUN_FOLDER)
            if file_name:
                rename_file_with_timestamp(RUN_FOLDER, file_name)
            else:
                failed_downloads.append(link.get_attribute("href"))

        # Process files
        unzip_files(RUN_FOLDER)
        organize_files_by_type(RUN_FOLDER)

        # Prepare email body
        success_msg = f"Reports successfully downloaded to {RUN_FOLDER}."
        failed_msg = f"Failed to download: {', '.join(failed_downloads)}" if failed_downloads else "No download failures."
        email_body = f"{success_msg}\n\n{failed_msg}"
        send_email("NSE Bot Report Send/Received", email_body, LOG_FILE)

    except TimeoutException:
        logging.error("Timeout while waiting for the element. Please check the locator or increase the timeout.")
    except Exception as e:
        logging.error(f"Error during execution: {e}")
    finally:
        driver.quit()
        logging.info("Files are verified and Report's download completed.")
        logging.info("WebDriver closed.")

# Execute the script
if __name__ == "__main__":
    main()
