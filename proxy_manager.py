import os
import zipfile
import requests
import random
import threading

class WebshareProxyManager:
    API_ENDPOINT = "https://proxy.webshare.io/api/v2/proxy/list/download/uihaxlzojvuevihxowldkahetcpwoelozpsiuipz/-/any/username/direct/-/"
    
    @staticmethod
    def fetch_proxies():
        try:
            response = requests.get(WebshareProxyManager.API_ENDPOINT)
            response.raise_for_status()
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
            return proxies
        except requests.RequestException as e:
            print(f"Error fetching Webshare proxies: {e}")
            return []

    @staticmethod
    def create_proxy_auth_extension(proxy_host, proxy_port, username, password, thread_id):
        # Create temp_extensions directory if it doesn't exist
        temp_dir = "temp_extensions"
        os.makedirs(temp_dir, exist_ok=True)

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

        extension_dir = os.path.join(temp_dir, f"proxy_auth_extension_thread_{thread_id}")
        os.makedirs(extension_dir, exist_ok=True)

        with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
            f.write(manifest_json)
        with open(os.path.join(extension_dir, "background.js"), "w") as f:
            f.write(background_js)

        extension_path = os.path.join(temp_dir, f"proxy_auth_extension_thread_{thread_id}.zip")
        with zipfile.ZipFile(extension_path, "w") as zf:
            zf.write(os.path.join(extension_dir, "manifest.json"), "manifest.json")
            zf.write(os.path.join(extension_dir, "background.js"), "background.js")

        return extension_path, extension_dir

    @staticmethod
    def cleanup_extension(extension_path, extension_dir):
        try:
            if os.path.exists(extension_path):
                os.remove(extension_path)
            if os.path.exists(extension_dir):
                for f in os.listdir(extension_dir):
                    os.remove(os.path.join(extension_dir, f))
                os.rmdir(extension_dir)
        except Exception as e:
            print(f"Error cleaning up extension files: {e}")

class ProxyManager:
    def __init__(self):
        self.all_proxies = WebshareProxyManager.fetch_proxies()
        self.used_proxies = set()
        self.lock = threading.Lock()

    def get_proxy(self):
        with self.lock:
            available_proxies = [p for p in self.all_proxies if tuple(p.items()) not in self.used_proxies]
            if not available_proxies:
                return None
            proxy = random.choice(available_proxies)
            self.used_proxies.add(tuple(proxy.items()))
            return proxy

    def mark_proxy_blocked(self, proxy_info):
        with self.lock:
            self.used_proxies.discard(tuple(proxy_info.items()))

    @staticmethod
    def setup_proxy_extension(proxy_info, thread_id):
        return WebshareProxyManager.create_proxy_auth_extension(
            proxy_info["host"], 
            proxy_info["port"],
            proxy_info["username"],
            proxy_info["password"],
            thread_id
        )
    
    @staticmethod
    def cleanup_proxy_resources(extension_path, extension_dir):
        WebshareProxyManager.cleanup_extension(extension_path, extension_dir)