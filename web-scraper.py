import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse
import os
import pandas as pd
import tiktoken
import openai
import numpy as np
from ast import literal_eval

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
        print(e)
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

# Function to crawl and scrape specified website
def crawl(url):
    # Parse the URL and get the domain
    local_domain = urlparse(url).netloc

    # Create a queue to store the URLs to crawl
    queue = deque([url])

    # Create a set to store the URLs that have already been seen (no duplicates)
    seen = set([url])

    # Create a directory to store the text files -> I think this is redundant? putting it here just in case
    if not os.path.exists("text/"):
        os.mkdir("text/")

    if not os.path.exists("text/"+local_domain+"/"):
        os.mkdir("text/" + local_domain + "/")

    # Create a directory to store the CSV files
    if not os.path.exists("ingested_data"):
        os.mkdir("ingested_data")

    # Counter to generate unique identifiers for file names
    file_counter = 1

    # Counter to keep track of the number of pages processed
    pages_processed = 0

    # Maximum number of pages to crawl | recommend starting with 10, increase based on performance
    # max_pages = 10
    max_pages = 1000000000000000000000000

    # While the queue is not empty, continue crawling
    #while queue:
    while queue and pages_processed < max_pages:

        # Get the next URL from the queue
        url = queue.pop()
        print(url) # for debugging and to see the progress | +1 for realtime updates :)

        # Try extracting the text from the link, if failed proceed with the next item in the queue
        try:
            # Generate a unique identifier for the file name (maximum of 10 characters)
            file_identifier = f"page_{file_counter:04}"[:10]

            # Increment the file counter
            file_counter += 1

            # Save text from the URL to a <file_identifier>.txt file
            with open(f'text/{local_domain}/{file_identifier}.txt', "w", encoding="UTF-8") as f:
                # Get the text from the URL using BeautifulSoup
                soup = BeautifulSoup(requests.get(url).text, "html.parser")

                # Get the text but remove the tags
                text = soup.get_text()

                # If the crawler gets to a page that requires JavaScript, it will stop the crawl
                if "You need to enable JavaScript to run this app." in text:
                    print(f"Unable to parse page {url} due to JavaScript being required")

                # Otherwise, write the text to the file in the text directory
                f.write(text)

            # Increment the pages_processed counter
            pages_processed += 1

        except Exception as e:
            print(f"Unable to parse page {url}")

        # Get the hyperlinks from the URL and add them to the queue
        for link in get_domain_hyperlinks(local_domain, url):
            if link not in seen:
                queue.append(link)
                seen.add(link)

crawl(full_url)

# Function to remove newlines from a Series
def remove_newlines(serie):
    serie = serie.str.replace('\n', ' ')
    serie = serie.str.replace('\\n', ' ')
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('  ', ' ')
    return serie

# Create a list to store the text files
texts = []

# Get all the text files in the text directory
for file in os.listdir(f"text/{domain}/"):
    # Open the file and read the text
    with open(f"text/{domain}/{file}", "r", encoding="UTF-8") as f:
        text = f.read()
        # Omit the first 11 lines and the last 4 lines, then replace -, _, and #update with spaces
        texts.append((file[11:-4].replace('-', ' ').replace('_', ' ').replace('#update', ''), text))

# Create a dataframe from the list of texts
df = pd.DataFrame(texts, columns=['fname', 'text'])

# Set the text column to be the raw text with the newlines removed
df['text'] = df.fname + ". " + remove_newlines(df.text)

# Save the DataFrame to a CSV file
df.to_csv('ingested_data/scraped.csv', escapechar='\\')

# Check if the CSV file was successfully saved
csv_file_path = 'ingested_data/scraped.csv'

if os.path.exists(csv_file_path):
    print(f"DataFrame successfully saved to {csv_file_path}")
else:
    print("Failed to save DataFrame to CSV")
