import threading
import time
import random
import os
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Webshare proxy list API endpoint
WEBSHARE_PROXY_LIST_URL = "https://proxy.webshare.io/api/v2/proxy/list/download/uihaxlzojvuevihxowldkahetcpwoelozpsiuipz/-/any/username/direct/-/"

# Function to fetch Webshare proxy list
def fetch_webshare_proxies():
    try:
        response = requests.get(WEBSHARE_PROXY_LIST_URL)
        response.raise_for_status()  # Raise an exception for bad status codes
        proxy_lines = response.text.strip().splitlines()
        proxies = []
        for line in proxy_lines:
            if line:
                host, port, username, password = line.split(':')
                proxies.append({
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": password
                })
        return proxies[:3]  # Return first 3 proxies for 3 threads
    except requests.RequestException as e:
        print(f"Error fetching Webshare proxies: {e}")
        return []

# Function to create a proxy authentication extension
def create_proxy_auth_extension(proxy_host, proxy_port, username, password, thread_id):
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth Extension",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        }
    }
    """

    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{proxy_host}",
                port: parseInt({proxy_port})
            }},
            bypassList: ["localhost"]
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

    chrome.webRequest.onAuthRequired.addListener(
        function(details) {{
            return {{
                authCredentials: {{
                    username: "{username}",
                    password: "{password}"
                }}
            }};
        }},
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """

    # Create a unique temporary directory for each thread
    extension_dir = f"proxy_auth_extension_thread_{thread_id}"
    os.makedirs(extension_dir, exist_ok=True)

    # Write manifest and background script
    with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
        f.write(manifest_json)
    with open(os.path.join(extension_dir, "background.js"), "w") as f:
        f.write(background_js)

    # Create a ZIP file for the extension
    extension_path = f"proxy_auth_extension_thread_{thread_id}.zip"
    with zipfile.ZipFile(extension_path, "w") as zf:
        zf.write(os.path.join(extension_dir, "manifest.json"), "manifest.json")
        zf.write(os.path.join(extension_dir, "background.js"), "background.js")

    return extension_path, extension_dir

# Function to open a tab, set proxy, and search
def search_with_proxy(proxy_info, thread_id, search_query):
    proxy_host = proxy_info["host"]
    proxy_port = proxy_info["port"]
    username = proxy_info["username"]
    password = proxy_info["password"]
    print(f"Thread {thread_id}: Starting with proxy {proxy_host}:{proxy_port}")

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--new-tab")  # Open in a new tab
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument(f"--proxy-server=http://{proxy_host}:{proxy_port}")

    # Add proxy authentication extension
    extension_path, extension_dir = create_proxy_auth_extension(proxy_host, proxy_port, username, password, thread_id)
    chrome_options.add_extension(extension_path)

    # Initialize WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Open Google
        driver.get("https://www.google.com")
        time.sleep(random.uniform(1, 3))  # Initial delay

        # Wait for the search box to be present
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")),
                                message="Search box not found; page might not have loaded correctly.")
        
        print(f"Thread {thread_id}: Successfully loaded Google homepage")

        # Enter query with human-like typing
        for char in search_query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))  # Typing delay
        time.sleep(random.uniform(0.5, 1.5))  # Pause before submitting

        # Submit search
        search_box.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2, 4))  # Wait for results

        print(f"Thread {thread_id}: Search completed for '{search_query}'")
        time.sleep(10)  # Keep browser open to observe

    except TimeoutException as e:
        print(f"Thread {thread_id}: Timeout - {str(e)}")
        print(f"Thread {thread_id}: Page title: {driver.title}")
        print(f"Thread {thread_id}: Partial page source: {driver.page_source[:500]}")
    except Exception as e:
        print(f"Thread {thread_id}: Error occurred - {str(e)}")
    
    finally:
        driver.quit()
        # Clean up extension files
        if os.path.exists(extension_path):
            os.remove(extension_path)
        if os.path.exists(extension_dir):
            for f in os.listdir(extension_dir):
                os.remove(os.path.join(extension_dir, f))
            os.rmdir(extension_dir)

# Main function to manage threads
def main():
    # Fetch Webshare proxies
    proxies = fetch_webshare_proxies()
    if not proxies or len(proxies) < 3:
        print("Failed to fetch enough proxies from Webshare. Exiting.")
        return

    search_query = input("Enter your search query: ").strip()
    if not search_query:
        print("Search query cannot be empty!")
        return

    threads = []
    for i, proxy in enumerate(proxies):  # Use first 3 proxies
        thread = threading.Thread(target=search_with_proxy, args=(proxy, i + 1, search_query))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("All searches completed!")

if __name__ == "__main__":
    main()