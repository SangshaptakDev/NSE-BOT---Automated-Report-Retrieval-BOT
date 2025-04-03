def logic():
    import os
    import time
    from datetime import datetime
    import csv
    import logging
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    import concurrent.futures

    # Set download path
    download_path = "C:\\NSE BOT MAIN\\Downloaded Report_extra"

    # Log file path
    log_file_path = r"C:\\NSE BOT MAIN\\nse text log extra.txt"


    # Remove previous log file if it exists
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
            logging.StreamHandler()  # Keeps logging in the console as well
        ]
    )
    logger = logging.getLogger(__name__)

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    prefs = {"download.default_directory": download_path}
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize WebDriver
    service = Service(ChromeDriverManager(driver_version="130.0.6723.117").install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    def wait_for_downloads_to_complete(download_path, expected_file_count):
        """
        Waits until the number of complete files in the download directory matches the expected count.
        Ignores temporary or incomplete files (e.g., .crdownload).
        """
        while True:
            files = [
                file for file in os.listdir(download_path)
                if os.path.isfile(os.path.join(download_path, file)) and not file.endswith(".crdownload")
            ]
            if len(files) >= expected_file_count:
                logger.info(f"All {expected_file_count} files downloaded.")
                break
            logger.info(f"Waiting for downloads to complete... Current count: {len(files)}/{expected_file_count}")
            time.sleep(2)

    def move_files_to_date_folder(download_path):
        """
        Moves all non-temporary files in the download path to a folder named with the current date.
        Retries moving files if some are temporarily locked.
        """
        today_date = datetime.now().strftime("%Y%m%d")
        target_folder = os.path.join(download_path, today_date)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        retries = 3
        for attempt in range(retries):
            files_moved = 0
            for file in os.listdir(download_path):
                file_path = os.path.join(download_path, file)
                if os.path.isfile(file_path) and not file.endswith(".crdownload"):
                    try:
                        new_path = os.path.join(target_folder, file)
                        os.rename(file_path, new_path)
                        logger.info(f"Moved file {file} to folder {today_date}")
                        files_moved += 1
                    except Exception as e:
                        logger.warning(f"Failed to move file {file} on attempt {attempt + 1}: {str(e)}")
            if files_moved > 0:
                break  # Exit loop if files are successfully moved
            time.sleep(5)  # Wait before retrying

    def validate_csv_file(file_path):
        """
        Validates if a given file is a properly formatted CSV.
        Returns True if valid, False otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    break  # If we can read the first row, it's a valid CSV
            logger.info(f"File '{file_path}' is a valid CSV.")
            return True
        except Exception as e:
            logger.error(f"File '{file_path}' is not a valid CSV: {str(e)}")
            return False

    def download_file(download_link, link_text):
        """
        Function to handle the downloading of each file.
        Tracks retry attempts and success/failure.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Scroll the link into view and click
                driver.execute_script("arguments[0].scrollIntoView(true);", download_link)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(download_link))
                driver.execute_script("arguments[0].click();", download_link)
                logger.info(f"Download attempt {attempt + 1} successful for file: {link_text}")
                return "Downloaded"
            except Exception as e:
                logger.warning(f"Retry {attempt + 1} for file {link_text} failed: {str(e)}")
                time.sleep(5)  # Wait before retrying
        return "Failed"

    try:
        # Navigate to the target page
        driver.get("https://www.nseindia.com/all-reports")

        # Explicit wait for page to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[11]/div[2]/div/section/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[1]/div/div[5]/div"))
            )
            logger.info("Page loaded and section found successfully.")
        except Exception as e:
            raise Exception("Page failed to load or section not found. Network issue or invalid URL.")

        # Locate the section with the download icons using the updated XPath
        try:
            current_date_section = driver.find_element(By.XPATH, "/html/body/div[11]/div[2]/div/section/div/div/div/div/div/div/div/div/div[2]/div/div[1]/div/div/div[1]/div/div[5]/div")
        except Exception as e:
            raise Exception(f"Could not locate the section. Error: {str(e)}")

        # Find all download links under this section
        download_links = current_date_section.find_elements(By.XPATH, ".//span/a")

        if download_links:
            logger.info(f"Found {len(download_links)} download links.")

            # Dictionary to track the download status
            download_status = {}

            # Start all downloads concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(download_file, link, link.text): link.text
                    for link in download_links
                }

                # Wait for all futures to complete
                for future in concurrent.futures.as_completed(futures):
                    link_text = futures[future]
                    try:
                        status = future.result()
                        download_status[link_text] = status
                    except Exception as e:
                        download_status[link_text] = "Failed"
                        logger.error(f"Unexpected error for file {link_text}: {str(e)}")

            # Display download summary
            logger.info("\nDownload Summary:")
            for file_name, status in download_status.items():
                if status == "Downloaded":
                    logger.info(f"[SUCCESS] {file_name}")
                elif status == "Failed":
                    logger.info(f"[FAILED] {file_name}")

            # Wait for all downloads to complete
            wait_for_downloads_to_complete(download_path, len(download_links))

            # Move all files into a folder named with today's date
            move_files_to_date_folder(download_path)
        else:
            logger.info("No download links found.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
    finally:
        time.sleep(10)  # Ensuring the browser stays open in case of an error for debugging purposes
        driver.quit()
