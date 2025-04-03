import os
import time
import logging
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Paths
DOWNLOAD_PATH = "C:\\NSE BOT MAIN\\Downloaded Report"
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
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
prefs = {"download.default_directory": DOWNLOAD_PATH}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize WebDriver
service = Service(ChromeDriverManager(driver_version="130.0.6723.117").install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def rename_file(file_path):
    """
    Rename a file to a simpler format: 1, 2, 3, etc., instead of (1), (2), etc.
    """
    base_name, ext = os.path.splitext(file_path)
    files = [f for f in os.listdir(DOWNLOAD_PATH) if f.startswith(base_name)]
    
    count = 1
    while f"{base_name} ({count}){ext}" in files:
        count += 1
    
    new_name = f"{base_name} ({count}){ext}"
    os.rename(file_path, os.path.join(DOWNLOAD_PATH, new_name))
    logging.info(f"Renamed file: {file_path} to {new_name}")
    return new_name

def unzip_file(file_path):
    """
    Unzips a file if it's a zip file and checks for CSV inside it.
    """
    if file_path.endswith(".zip"):
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(DOWNLOAD_PATH)
                logging.info(f"Unzipped file: {file_path}")
                # After unzipping, check for CSV files
                for extracted_file in zip_ref.namelist():
                    if not extracted_file.endswith('.csv'):
                        os.remove(os.path.join(DOWNLOAD_PATH, extracted_file))
                        logging.info(f"Deleted non-CSV file: {extracted_file}")
        except Exception as e:
            logging.error(f"Failed to unzip {file_path}: {e}")
            return False
    return True

def is_csv(file_name):
    """
    Check if the file is a CSV file.
    """
    return file_name.endswith(".csv")

def clean_up_files():
    """
    Clean up any non-CSV files and ensure all CSV files are correctly renamed.
    """
    for file_name in os.listdir(DOWNLOAD_PATH):
        file_path = os.path.join(DOWNLOAD_PATH, file_name)
        if os.path.isdir(file_path):
            continue

        if is_csv(file_name):
            if file_name.count("(") > 1:  # Check if the file name has duplicate numbering
                rename_file(file_path)
        else:
            os.remove(file_path)
            logging.info(f"Deleted non-CSV file: {file_name}")

def download_file(download_link, download_path):
    """
    Function to download a single file and wait for it to complete.
    """
    try:
        initial_files = os.listdir(download_path)
        driver.execute_script("arguments[0].scrollIntoView(true);", download_link)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(download_link))
        driver.execute_script("arguments[0].click();", download_link)
        logging.info(f"Clicked on download link: {download_link.get_attribute('href')}")
        
        if is_file_downloaded(download_path, initial_files):
            logging.info("File downloaded successfully.")
            return True
        else:
            logging.warning("File download timed out.")
            return False
    except Exception as e:
        logging.error(f"Error downloading file: {str(e)}")
        return False

def is_file_downloaded(download_path, initial_files, timeout=60):
    """
    Checks if a new file appears in the download directory within the timeout period.
    """
    seconds = 0
    while seconds < timeout:
        files = os.listdir(download_path)
        new_files = set(files) - set(initial_files)
        if new_files:
            for file in new_files:
                if not file.endswith(".crdownload"):
                    return True
        time.sleep(1)
        seconds += 1
    return False

def main():
    try:
        # Navigate to the target page
        driver.get("https://www.nseindia.com/all-reports")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.XPATH, "/html/body/div[11]/div[2]/div/section/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[1]/div/div[5]/div")
        ))
        logging.info("Page loaded and section found successfully.")
        
        # Locate the section with download icons
        current_date_section = driver.find_element(By.XPATH, "/html/body/div[11]/div[2]/div/section/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[1]/div/div[5]/div")
        download_links = current_date_section.find_elements(By.XPATH, ".//span/a")
        
        if download_links:
            logging.info(f"Found {len(download_links)} download links.")
            failed_downloads = 0
            for link in download_links:
                if not download_file(link, DOWNLOAD_PATH):
                    failed_downloads += 1
                    logging.warning("Failed to download a file.")
                    if failed_downloads >= 3:
                        logging.error("Max retry limit reached. Aborting script.")
                        break

            # Clean up and verify files
            clean_up_files()
            logging.info("Files are verified for CSV and unnecessary files are deleted.")
            logging.info("All download attempts completed.")
        else:
            logging.warning("No download links found.")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        # Ensure browser is closed even after exceptions
        time.sleep(10)
        driver.quit()
        logging.info("Script has completed.")
        logging.shutdown()  # Ensures logs are flushed to file

# Call main function
main()
