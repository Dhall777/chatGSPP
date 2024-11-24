from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080")

    service = Service(executable_path='/usr/local/bin/chromedriver')  # Update if different

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com")
        print("Title:", driver.title)
        driver.quit()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_webdriver()
