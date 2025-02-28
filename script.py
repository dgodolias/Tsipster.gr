import threading
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from proxy_manager import ProxyManager

def is_captcha_page(driver):
    """Check if the page is a CAPTCHA by looking for specific elements or text"""
    try:
        title = driver.title.lower()
        source = driver.page_source.lower()
        return "captcha" in title or "recaptcha" in source or "unusual traffic" in source
    except Exception:
        return False

def is_consent_page(driver):
    """Check if the page is the Google consent screen by looking for the 'Reject All' button"""
    try:
        driver.find_element(By.ID, "W0wltc")
        return True
    except NoSuchElementException:
        return False

def handle_consent_page(driver, thread_id):
    """Handle the consent page by clicking 'Reject All'"""
    try:
        wait = WebDriverWait(driver, 5)
        reject_button = wait.until(EC.element_to_be_clickable((By.ID, "W0wltc")))
        reject_button.click()
        print(f"Thread {thread_id}: Consent screen detected and 'Reject All' clicked")
        time.sleep(random.uniform(1, 2))  # Wait for page to proceed
    except TimeoutException:
        print(f"Thread {thread_id}: Consent screen detected but 'Reject All' button not clickable")

def extract_urls(driver, thread_id):
    """Extract URLs from Google search results"""
    urls = []
    try:
        # Find all search result containers
        results = driver.find_elements(By.CSS_SELECTOR, "div.g.Ww4FFb.vt6azd.tF2Cxc.asEBEc")
        for result in results:
            # Extract the URL from the 'a' tag with jsname="UWckNb"
            link = result.find_element(By.XPATH, ".//a[@jsname='UWckNb']")
            url = link.get_attribute("href")
            urls.append(url)
        print(f"Thread {thread_id}: Extracted {len(urls)} URLs: {urls}")
    except Exception as e:
        print(f"Thread {thread_id}: Error extracting URLs - {str(e)}")
    return urls

def visit_website(driver, url, thread_id):
    """Visit a single website and wait briefly"""
    try:
        print(f"Thread {thread_id}: Visiting {url}")
        driver.get(url)
        time.sleep(random.uniform(2, 5))  # Wait to simulate browsing
        print(f"Thread {thread_id}: Successfully visited {url}")
    except Exception as e:
        print(f"Thread {thread_id}: Error visiting {url} - {str(e)}")

def init_driver(proxy_info, thread_id):
    """Initialize a WebDriver instance with proxy settings"""
    proxy_host = proxy_info["host"]
    proxy_port = proxy_info["port"]
    print(f"Thread {thread_id}: Initializing driver with proxy {proxy_host}:{proxy_port}")

    chrome_options = Options()
    chrome_options.add_argument("--new-tab")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")

    extension_path, extension_dir = ProxyManager.setup_proxy_extension(proxy_info, thread_id)
    chrome_options.add_extension(extension_path)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver, extension_path, extension_dir

def search_with_proxy(proxy_manager, thread_id, search_query, max_attempts=3):
    """Run a search and visit extracted URLs using a proxy, retrying if blocked"""
    attempt = 0
    driver = None
    extension_path = None
    extension_dir = None

    while attempt < max_attempts:
        proxy_info = proxy_manager.get_proxy()
        if not proxy_info:
            print(f"Thread {thread_id}: No available proxies left!")
            return

        # Initialize driver for this attempt
        if driver:
            driver.quit()
            ProxyManager.cleanup_proxy_resources(extension_path, extension_dir)
        driver, extension_path, extension_dir = init_driver(proxy_info, thread_id)

        try:
            # Navigate to Google
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 5))

            # Check for CAPTCHA
            if is_captcha_page(driver):
                print(f"Thread {thread_id}: CAPTCHA detected with proxy {proxy_info['host']}:{proxy_info['port']}")
                proxy_manager.mark_proxy_blocked(proxy_info)
                attempt += 1
                continue

            # Handle consent screen if present
            if is_consent_page(driver):
                handle_consent_page(driver, thread_id)

            # Wait for search box
            wait = WebDriverWait(driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")),
                                    message="Search box not found; page might not have loaded correctly.")
            
            print(f"Thread {thread_id}: Successfully loaded Google homepage")

            # Type and submit search query
            for char in search_query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            time.sleep(random.uniform(0.5, 1.5))
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(2, 4))

            # Check for CAPTCHA after search
            if is_captcha_page(driver):
                print(f"Thread {thread_id}: CAPTCHA detected after search with proxy {proxy_info['host']}:{proxy_info['port']}")
                proxy_manager.mark_proxy_blocked(proxy_info)
                attempt += 1
                continue

            print(f"Thread {thread_id}: Search completed for '{search_query}'")

            # Extract URLs and visit each site
            urls = extract_urls(driver, thread_id)
            for url in urls:
                visit_website(driver, url, thread_id)

            break

        except TimeoutException as e:
            print(f"Thread {thread_id}: Timeout - {str(e)}")
            print(f"Thread {thread_id}: Page title: {driver.title if driver else 'N/A'}")
            print(f"Thread {thread_id}: Partial page source: {driver.page_source[:500] if driver else 'N/A'}")
            proxy_manager.mark_proxy_blocked(proxy_info)
            attempt += 1
        except WebDriverException as e:
            print(f"Thread {thread_id}: WebDriver error - {str(e)}")
            proxy_manager.mark_proxy_blocked(proxy_info)
            attempt += 1
        finally:
            # Cleanup is handled after each attempt, driver is recreated if retrying
            pass

    if attempt >= max_attempts:
        print(f"Thread {thread_id}: Failed after {max_attempts} attempts with different proxies")
    if driver:
        driver.quit()
        ProxyManager.cleanup_proxy_resources(extension_path, extension_dir)

def main():
    """Main function to run the search bot concurrently"""
    proxy_manager = ProxyManager()
    if not proxy_manager.all_proxies:
        print("Failed to fetch proxies. Exiting.")
        return

    search_query = input("Enter your search query: ").strip()
    if not search_query:
        print("Search query cannot be empty!")
        return

    # Start threads concurrently
    threads = []
    for i in range(3):
        thread = threading.Thread(target=search_with_proxy, args=(proxy_manager, i + 1, search_query))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All searches and site visits completed!")
    print(f"Total proxies used: {len(proxy_manager.used_proxies)}")

if __name__ == "__main__":
    main()