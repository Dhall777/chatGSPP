import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse, quote
import os
import pandas as pd

# Regex pattern to match a URL
HTTP_URL_PATTERN = r'^http[s]{0,1}://.+$'

# Define root domain to crawl
domain = "gspp.berkeley.edu"
full_url = "https://gspp.berkeley.edu/"

# Parse the URL and get the domain
local_domain = urlparse(full_url).netloc

# Create a directory to store the text files (sorted by domain)
if not os.path.exists("text/"):
    os.mkdir("text/")

if not os.path.exists(f"text/{local_domain}/"):
    os.mkdir(f"text/{local_domain}/")

# Create a directory to store the CSV files
if not os.path.exists("ingested_data"):
    os.mkdir("ingested_data")

# Create a class to parse the HTML and get the hyperlinks
class HyperlinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        # Create a list to store the hyperlinks
        self.hyperlinks = []

    # Override the HTMLParser's handle_starttag method to get the hyperlinks
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        # If the tag is an anchor tag and it has an href attribute, add the href attribute to the list of hyperlinks
        if tag == "a" and "href" in attrs:
            self.hyperlinks.append(attrs["href"])

# Function to get the hyperlinks from a URL
def get_hyperlinks(url):
    try:
        # Open the URL and read the HTML
        with urllib.request.urlopen(url) as response:

            # If the response is not HTML, return an empty list
            if not response.info().get('Content-Type').startswith("text/html"):
                return []

            # Decode the HTML
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error opening URL: {e}")
        return []

    # Create the HTML Parser and then Parse the HTML to get hyperlinks
    parser = HyperlinkParser()
    parser.feed(html)

    return parser.hyperlinks

# Function to get the hyperlinks from a URL that are within the same domain
def get_domain_hyperlinks(local_domain, url):
    clean_links = []
    for link in set(get_hyperlinks(url)):
        clean_link = None

        # If the link is a URL, check if it is within the same domain
        if re.search(HTTP_URL_PATTERN, link):
            # Parse the URL and check if the domain is the same
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link

        # If the link is not a URL, check if it is a relative link
        else:
            if link.startswith("/"):
                link = link[1:]
            elif (
                link.startswith("#")
                or link.startswith("mailto:")
                or link.startswith("tel:")
            ):
                continue
            clean_link = "https://" + local_domain + "/" + link

        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)

    # Return the list of hyperlinks that are within the same domain
    return list(set(clean_links))

# Sanitize URL to be used as a file name
def sanitize_filename(url):
    # Remove protocol and replace special characters with underscores
    safe_url = re.sub(r'[^\w\-_\. ]', '_', url.replace("https://", "").replace("http://", ""))
    return safe_url

# Function to crawl and scrape specified website
def crawl(url):
    # Parse the URL and get the domain
    local_domain = urlparse(url).netloc

    # Create a queue to store the URLs to crawl
    queue = deque([url])

    # Create a set to store the URLs that have already been seen (no duplicates)
    seen = set([url])

    # Maximum number of pages to crawl
    max_pages = 100000000000

    # Counter to keep track of the number of pages processed
    pages_processed = 0

    # While the queue is not empty, continue crawling
    while queue and pages_processed < max_pages:

        # Get the next URL from the queue
        url = queue.pop()
        print(url) # for debugging and to see the progress | +1 for realtime updates :)

        # Try extracting the text from the link, if failed proceed with the next item in the queue
        try:
            # Generate a unique identifier for the file name based on the URL
            file_identifier = sanitize_filename(url)

            # Save text from the URL to a <file_identifier>.txt file
            with open(f'text/{local_domain}/{file_identifier}.txt', "w", encoding="UTF-8") as f:
                # Get the text from the URL using BeautifulSoup
                soup = BeautifulSoup(requests.get(url).text, "html.parser")

                # Get the text but remove the tags
                text = soup.get_text()

                # Clean the text by removing newlines and extra spaces
                cleaned_text = " ".join(text.split())

                # If the crawler gets to a page that requires JavaScript, it will stop the crawl
                if "You need to enable JavaScript to run this app." in text:
                    print(f"Unable to parse page {url} due to JavaScript being required")

                # Otherwise, write the cleaned text to the file in the text directory
                f.write(cleaned_text)

            # Create a DataFrame for the page
            df = pd.DataFrame([[url, cleaned_text]], columns=['fname', 'text'])

            # Save each page as a separate CSV file with the URL as the filename
            csv_filename = f'ingested_data/{file_identifier}.csv'
            df.to_csv(csv_filename, escapechar='\\', index=False)
            print(f"Saved CSV: {csv_filename}")

            # Increment the pages_processed counter
            pages_processed += 1

        except Exception as e:
            print(f"Unable to parse page {url}: {e}")

        # Get the hyperlinks from the URL and add them to the queue
        for link in get_domain_hyperlinks(local_domain, url):
            if link not in seen:
                queue.append(link)
                seen.add(link)

# Start the crawl
crawl(full_url)
