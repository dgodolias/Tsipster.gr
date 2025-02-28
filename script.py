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
from selenium.common.exceptions import TimeoutException

from proxy_manager import ProxyManager

def search_with_proxy(proxy_info, thread_id, search_query):
    """Run a search using a proxy"""
    proxy_host = proxy_info["host"]
    proxy_port = proxy_info["port"]
    print(f"Thread {thread_id}: Starting with proxy {proxy_host}:{proxy_port}")

    chrome_options = Options()
    chrome_options.add_argument("--new-tab")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")

    extension_path, extension_dir = ProxyManager.setup_proxy_extension(proxy_info, thread_id)
    chrome_options.add_extension(extension_path)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Navigate to Google
        driver.get("https://www.google.com")
        time.sleep(random.uniform(1, 3))

        # Wait for search box to appear
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")),
                                message="Search box not found; page might not have loaded correctly.")
        
        print(f"Thread {thread_id}: Successfully loaded Google homepage")

        # Type search query with realistic timing
        for char in search_query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        time.sleep(random.uniform(0.5, 1.5))

        # Submit search
        search_box.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2, 4))

        print(f"Thread {thread_id}: Search completed for '{search_query}'")
        time.sleep(10)  # Keep the browser open for a while to see results

    except TimeoutException as e:
        print(f"Thread {thread_id}: Timeout - {str(e)}")
        print(f"Thread {thread_id}: Page title: {driver.title}")
        print(f"Thread {thread_id}: Partial page source: {driver.page_source[:500]}")
    except Exception as e:
        print(f"Thread {thread_id}: Error occurred - {str(e)}")
    
    finally:
        driver.quit()
        ProxyManager.cleanup_proxy_resources(extension_path, extension_dir)

def main():
    """Main function to run the search bot"""
    # Get proxies from the configured provider
    proxies = ProxyManager.get_proxies(3)
    if not proxies or len(proxies) < 1:
        print("Failed to fetch enough proxies. Exiting.")
        return

    # Get search query from user
    search_query = input("Enter your search query: ").strip()
    if not search_query:
        print("Search query cannot be empty!")
        return

    # Start a thread for each proxy
    threads = []
    for i, proxy in enumerate(proxies):
        thread = threading.Thread(target=search_with_proxy, args=(proxy, i + 1, search_query))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All searches completed!")

if __name__ == "__main__":
    main()