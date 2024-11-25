import signal
import sys
import re
import os
import time
import logging
from urllib.parse import urlparse
import pandas as pd
from multiprocessing import Process, Manager, current_process
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from logging.handlers import QueueHandler, QueueListener
import hashlib
from queue import Empty  # Import the Empty exception

# -------------------- Signal Handling --------------------

# Graceful shutdown when terminated with SIGINT [Ctrl+C] and SIGTERM [kill]
def signal_handler(sig, frame):
    logging.info('Interrupt received, shutting down...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# -------------------- Configuration --------------------

# Regex pattern to match a URL
HTTP_URL_PATTERN = r'^http[s]?://.+$'

# Define root domain to crawl
DOMAIN = "gspp.berkeley.edu"
FULL_URL = "https://gspp.berkeley.edu/"

# Parse the URL and get the domain
LOCAL_DOMAIN = urlparse(FULL_URL).netloc

# Directories to store data
TEXT_DIR = f"text/{LOCAL_DOMAIN}/"
CSV_DIR = "ingested_data/"

# Ensure directories exist
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

# Maximum number of pages to crawl
MAX_PAGES = 100000000000  # Adjust as needed

# Crawl delay (in seconds) to be respectful to the server
CRAWL_DELAY = 3  # Adjust as needed

# Path to ChromeDriver (if not in PATH, specify the full path)
CHROMEDRIVER_PATH = '/usr/local/bin/chromedriver'  # Replace with your path if necessary

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # Seconds to wait before retrying

# Number of worker processes
MAX_WORKERS = 10  # Start with 1 for testing, increase as needed

# User-Agent string
USER_AGENT = "GsppCrawler/1.0 (+http://www.example.com/crawler)"

# --------------------------------------------------------

# -------------------- Logging Setup --------------------

def setup_logging(log_queue):
    """
    Sets up logging to listen to a multiprocessing queue.
    Logs are written to both console and a log file.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create handlers
    file_handler = logging.FileHandler("local_data/logs/crawler.log")
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Create QueueListener
    listener = QueueListener(log_queue, file_handler, console_handler)
    listener.start()

    return listener

# --------------------------------------------------------

# -------------------- Selenium WebDriver Setup --------------------

def init_webdriver():
    """
    Initializes and returns a headless Selenium WebDriver.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument(f"user-agent={USER_AGENT}")  # Set custom User-Agent
    chrome_options.add_argument("window-size=1920,1080")  # Ensure all elements load

    # Initialize the Service object with the path to chromedriver
    service = Service(executable_path=CHROMEDRIVER_PATH)

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)  # Set timeout for page load
        return driver
    except WebDriverException as e:
        logging.error(f"Error initializing WebDriver: {e}")
        raise e

# -----------------------------------------------------------------

# -------------------- Utility Functions --------------------

def sanitize_filename(url):
    """
    Converts a URL into a filesystem-friendly filename by removing protocols,
    replacing special characters, and removing the hash for readability.
    """
    url = url.rstrip('/')  # Remove trailing slash
    # Remove the protocol (http:// or https://)
    url_no_protocol = re.sub(r'^http[s]?://', '', url)
    # Remove query parameters and fragments
    url_no_protocol = url_no_protocol.split('?')[0].split('#')[0]
    # Replace all non-word characters with underscores
    safe_url = re.sub(r'[^\w\-_\. ]', '_', url_no_protocol)
    return safe_url

def extract_hyperlinks(soup):
    """
    Extracts all unique hyperlinks from the BeautifulSoup-parsed HTML.
    """
    hyperlinks = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        hyperlinks.add(href)
    return hyperlinks

def get_domain_hyperlinks(local_domain, hyperlinks):
    """
    Filters and cleans hyperlinks to include only those within the same domain.
    """
    clean_links = set()
    for link in hyperlinks:
        clean_link = None

        # If the link is an absolute URL, check if it's within the same domain
        if re.match(HTTP_URL_PATTERN, link):
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link
        else:
            # Handle relative URLs
            if link.startswith("/"):
                clean_link = f"https://{local_domain}{link}"
            elif not (link.startswith("#") or link.startswith("mailto:") or link.startswith("tel:")):
                # Other relative links without leading slash
                clean_link = f"https://{local_domain}/{link}"

        if clean_link:
            # Remove trailing slash for consistency
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.add(clean_link)

    return list(clean_links)

# --------------------------------------------------------------

# -------------------- Crawling Function --------------------

def crawl(url, driver, queue, seen, pages_processed, log_queue):
    """
    Crawls the given URL, extracts text, saves data, and queues internal links.
    Implements retry logic for robustness.
    """
    logger = logging.getLogger(current_process().name)
    logger.addHandler(QueueHandler(log_queue))
    logger.setLevel(logging.INFO)

    logger.info(f"Crawling ({pages_processed.value + 1}): {url}")
    retries = 0

    while retries < MAX_RETRIES:
        try:
            driver.get(url)

            # Wait until the <body> tag is present, indicating the page has loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Get the rendered HTML
            rendered_html = driver.page_source

            # Parse with BeautifulSoup
            soup = BeautifulSoup(rendered_html, "html.parser")

            # Extract text content
            text = soup.get_text(separator=" ", strip=True)
            cleaned_text = " ".join(text.split())

            # Check for JavaScript requirement message
            if "You need to enable JavaScript to run this app." in cleaned_text:
                logger.warning(f"Skipped (JavaScript required): {url}")
                return

            # Sanitize filename
            file_identifier = sanitize_filename(url)

            # Save text to file
            text_filepath = os.path.join(TEXT_DIR, f"{file_identifier}.txt")
            with open(text_filepath, "w", encoding="UTF-8") as f:
                f.write(cleaned_text)
            logger.info(f"Saved Text: {text_filepath}")

            # Save URL and text to CSV
            df = pd.DataFrame([[url, cleaned_text]], columns=['fname', 'text'])
            csv_filename = os.path.join(CSV_DIR, f"{file_identifier}.csv")
            df.to_csv(csv_filename, escapechar='\\', index=False)
            logger.info(f"Saved CSV: {csv_filename}")

            # Increment pages_processed
            pages_processed.value += 1
            logger.info(f"Pages Processed: {pages_processed.value}")

            # Extract and process hyperlinks
            hyperlinks = extract_hyperlinks(soup)
            logger.info(f"Extracted {len(hyperlinks)} hyperlinks from {url}")

            domain_links = get_domain_hyperlinks(LOCAL_DOMAIN, hyperlinks)
            logger.info(f"Filtered {len(domain_links)} domain-specific links from {url}")

            new_links = 0
            for link in domain_links:
                if link not in seen:
                    queue.put(link)
                    seen[link] = True  # Mark as seen when enqueuing
                    new_links += 1
                    logger.info(f"Enqueued new link: {link}")

            logger.info(f"Total new links enqueued from {url}: {new_links}")

            # Respectful crawling delay
            time.sleep(CRAWL_DELAY)
            return  # Successfully processed

        except TimeoutException:
            retries += 1
            logger.warning(f"Timeout loading {url}. Retry {retries}/{MAX_RETRIES}")
            time.sleep(RETRY_DELAY)
        except WebDriverException as e:
            retries += 1
            logger.error(f"Selenium error on {url}: {e}. Retry {retries}/{MAX_RETRIES}")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Unexpected error processing {url}: {e}. Skipping...")
            return  # Skip on unexpected errors

    logger.error(f"Failed to process {url} after {MAX_RETRIES} retries.")

# -----------------------------------------------------------------

# -------------------- Worker Process --------------------

def worker(url_queue, seen, pages_processed, log_queue):
    """
    Worker process that continuously crawls URLs from the queue.
    """
    # Set up logging for the worker
    logger = logging.getLogger(current_process().name)
    logger.setLevel(logging.INFO)
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)
    logger.propagate = False  # Prevent logs from propagating to the root logger

    # Initialize WebDriver
    try:
        driver = init_webdriver()
    except Exception as e:
        logger.error(f"WebDriver initialization failed: {e}")
        return

    while True:
        try:
            url = url_queue.get(timeout=5)  # Wait up to 5 seconds for a URL
        except Empty:
            # Queue is empty for 5 seconds, assume crawling is done
            break
        except Exception as e:
            logger.error(f"Error getting URL from queue: {e}")
            break

        if pages_processed.value >= MAX_PAGES:
            break

        # No need to check 'if url in seen: skip' since 'seen' is marked when enqueuing
        # No duplicate enqueues should occur

        # Crawl the URL
        crawl(url, driver, url_queue, seen, pages_processed, log_queue)

    # Clean up
    driver.quit()
    logger.info("Worker exiting.")

# --------------------------------------------------------------

# -------------------- Main Execution --------------------

def main():
    # Create a Manager for shared data structures
    manager = Manager()
    url_queue = manager.Queue()
    seen = manager.dict()
    pages_processed = manager.Value('i', 0)

    # Initialize logging queue
    log_queue = manager.Queue()

    # Set up logging listener
    listener = setup_logging(log_queue)

    # Initialize the queue with the start URL
    url_queue.put(FULL_URL)
    # Remove the following line to allow workers to process the start URL
    # seen[FULL_URL] = True

    # Create worker processes
    workers = []
    for _ in range(MAX_WORKERS):
        p = Process(target=worker, args=(url_queue, seen, pages_processed, log_queue))
        p.start()
        workers.append(p)

    # Wait for all workers to finish
    for p in workers:
        p.join()

    # Stop the logging listener
    listener.stop()

    logging.info("Crawling completed.")

# --------------------------------------------------------------

# Run main
if __name__ == "__main__":
    main()
