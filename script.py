import threading
import time
import random
import os
import shutil
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

# Country-specific settings (Greece)
EU_COUNTRIES = [{"country_code": "GR", "domain": "google.gr", "lang": "el", "currency": "EUR"}]
COUNTRY = EU_COUNTRIES[0]

# Global tracking for visited pages and max pages
visited_pages = set()
page_lock = threading.Lock()
current_start = -10  # Start before page 1
max_start = None

def is_captcha_page(driver):
    try:
        title = driver.title.lower()
        source = driver.page_source.lower()
        return "captcha" in title or "recaptcha" in source or "unusual traffic" in source
    except Exception:
        return False

def is_consent_page(driver):
    try:
        driver.find_element(By.ID, "W0wltc")
        return True
    except NoSuchElementException:
        return False

def handle_consent_page(driver, thread_id):
    try:
        wait = WebDriverWait(driver, 5)
        reject_button = wait.until(EC.element_to_be_clickable((By.ID, "W0wltc")))
        reject_button.click()
        print(f"Thread {thread_id}: Consent screen detected and 'Reject All' clicked")
        time.sleep(random.uniform(1, 2))
    except TimeoutException:
        print(f"Thread {thread_id}: Consent screen detected but 'Reject All' button not clickable")

def get_max_pages(driver):
    try:
        nav = driver.find_element(By.CSS_SELECTOR, "div[role='navigation'] table.AaVjTc")
        page_links = nav.find_elements(By.XPATH, ".//a[contains(@aria-label, 'Page')]")
        if page_links:
            last_page = int(page_links[-1].text.strip())
            return (last_page - 1) * 10
        return 0
    except Exception:
        print(f"Thread: Could not determine max pages, assuming single page")
        return 0

def extract_urls(driver, thread_id):
    urls = []
    try:
        results = driver.find_elements(By.CSS_SELECTOR, "div.g.Ww4FFb.vt6azd.tF2Cxc.asEBEc")
        for result in results:
            link = result.find_element(By.XPATH, ".//a[@jsname='UWckNb']")
            url = link.get_attribute("href")
            urls.append(url)
        print(f"Thread {thread_id}: URLs to visit from this page: {urls}")
    except Exception as e:
        print(f"Thread {thread_id}: Error extracting URLs - {str(e)}")
    return urls

def visit_website(driver, url, thread_id):
    try:
        print(f"Thread {thread_id}: Visiting {url}")
        driver.get(url)
        time.sleep(random.uniform(2, 5))
        print(f"Thread {thread_id}: Successfully visited {url}")
    except WebDriverException as e:
        print(f"Thread {thread_id}: Error visiting {url} - {str(e)}")

def get_next_page():
    global current_start, max_start
    with page_lock:
        current_start += 10
        while current_start in visited_pages or (max_start is not None and current_start > max_start):
            current_start += 10
            if max_start is not None and current_start > max_start:
                current_start = -10
                while current_start in visited_pages and current_start <= max_start:
                    current_start += 10
                if current_start > max_start:
                    return None
        visited_pages.add(current_start)
        return current_start

def init_driver(proxy_info, thread_id):
    proxy_host = proxy_info["host"]
    proxy_port = proxy_info["port"]
    print(f"Thread {thread_id}: Initializing driver with proxy {proxy_host}:{proxy_port}")

    chrome_options = Options()
    chrome_options.add_argument("--new-tab")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")

    try:
        extension_path, extension_dir = ProxyManager.setup_proxy_extension(proxy_info, thread_id)
        chrome_options.add_extension(extension_path)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver, extension_path, extension_dir
    except Exception as e:
        print(f"Thread {thread_id}: Failed to initialize driver - {str(e)}")
        raise

def search_with_proxy(proxy_manager, thread_id, search_query):
    driver = None
    extension_path = None
    extension_dir = None
    attempt = 0

    while True:
        attempt += 1
        proxy_info = proxy_manager.get_proxy()
        if not proxy_info:
            print(f"Thread {thread_id}: No available proxies left after {attempt-1} attempts!")
            return

        if driver:
            driver.quit()
            ProxyManager.cleanup_proxy_resources(extension_path, extension_dir)
        try:
            driver, extension_path, extension_dir = init_driver(proxy_info, thread_id)
        except Exception as e:
            print(f"Thread {thread_id}: Attempt {attempt}: Proxy initialization failed with {proxy_info['host']}:{proxy_info['port']} - retrying")
            proxy_manager.mark_proxy_blocked(proxy_info)
            time.sleep(1)
            continue

        start = get_next_page()
        if start is None:
            print(f"Thread {thread_id}: No more unvisited pages available after {attempt} attempts")
            break

        search_url = f"https://{COUNTRY['domain']}/search?q={search_query}&start={start}&hl={COUNTRY['lang']}&gl={COUNTRY['country_code']}&cr=country{COUNTRY['country_code']}"

        try:
            print(f"Thread {thread_id}: Attempt {attempt}: Navigating to {search_url}")
            driver.get(search_url)
            time.sleep(random.uniform(2, 5))

            if is_captcha_page(driver):
                print(f"Thread {thread_id}: Attempt {attempt}: CAPTCHA detected with proxy {proxy_info['host']}:{proxy_info['port']} on page start={start}")
                proxy_manager.mark_proxy_blocked(proxy_info)
                with page_lock:
                    visited_pages.remove(start)
                continue

            if is_consent_page(driver):
                handle_consent_page(driver, thread_id)

            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#search")),
                       message="Search results not found; page might not have loaded correctly.")
            
            print(f"Thread {thread_id}: Successfully loaded Google page with start={start}")

            global max_start
            if max_start is None:
                with page_lock:
                    if max_start is None:
                        max_start = get_max_pages(driver)
                        print(f"Thread {thread_id}: Determined max_start={max_start}")

            urls = extract_urls(driver, thread_id)
            for url in urls:
                visit_website(driver, url, thread_id)

            break

        except TimeoutException as e:
            print(f"Thread {thread_id}: Attempt {attempt}: Timeout - {str(e)} on page start={start}")
            print(f"Thread {thread_id}: Page title: {driver.title if driver else 'N/A'}")
            print(f"Thread {thread_id}: Partial page source: {driver.page_source[:500] if driver else 'N/A'}")
            proxy_manager.mark_proxy_blocked(proxy_info)
            with page_lock:
                visited_pages.remove(start)
        except WebDriverException as e:
            print(f"Thread {thread_id}: Attempt {attempt}: WebDriver error - {str(e)} on page start={start}")
            proxy_manager.mark_proxy_blocked(proxy_info)
            with page_lock:
                visited_pages.remove(start)
        finally:
            pass

    if driver:
        driver.quit()
        ProxyManager.cleanup_proxy_resources(extension_path, extension_dir)

def main():
    # Create temp_extensions directory
    temp_dir = "temp_extensions"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        proxy_manager = ProxyManager()
        if not proxy_manager.all_proxies:
            print("Failed to fetch proxies. Exiting.")
            return

        search_query = input("Enter your search query: ").strip()
        if not search_query:
            print("Search query cannot be empty!")
            return

        threads = []
        for i in range(3):
            thread = threading.Thread(target=search_with_proxy, args=(proxy_manager, i + 1, search_query))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print("All searches and site visits completed!")
        print(f"Total proxies used: {len(proxy_manager.used_proxies)}")
        print(f"Visited pages (start values): {sorted(visited_pages)}")

    finally:
        # Clean up temp_extensions directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"Cleaned up {temp_dir} directory")
        except Exception as e:
            print(f"Error cleaning up {temp_dir}: {e}")

if __name__ == "__main__":
    main()