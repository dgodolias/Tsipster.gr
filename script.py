from playwright.sync_api import sync_playwright
import random
import time

def google_search(query):
    """
    Perform a Google search using Playwright.
    
    Args:
        query (str): The search query to enter
    """
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=True)  # Set headless=True to reduce detection
        page = browser.new_page()
        
        # Navigate to Google
        print(f"Navigating to Google...")
        page.goto('https://www.google.com')
        
        # Accept cookies if the dialog appears
        if page.locator('button:has-text("Αποδοχή όλων")').is_visible():
            page.locator('button:has-text("Αποδοχή όλων")').click()
            print("Accepted cookies")
            time.sleep(random.uniform(1, 3))  # Random delay
        
        # Find the search input field and type the query
        print(f"Entering search query: {query}")
        search_input = page.locator('textarea#APjFqb')  # Correct selector for the search input field
        
        # Ensure the search input is visible before clicking
        if search_input.is_visible():
            search_input.click()
            search_input.fill(query)
            time.sleep(random.uniform(1, 3))  # Random delay
            # Press Enter to search
            search_input.press('Enter')
            print("Performing search...")
            
            # Wait for the search results to load
            page.wait_for_load_state('networkidle')
            print("Search results loaded")
            
            # You can add additional code here to scrape search results if needed
            
            # Pause to see the results (remove in production)
            print("Waiting 5 seconds before closing...")
            page.wait_for_timeout(5000)
        else:
            print("Search input field not found or not visible.")
        
        # Close the browser
        browser.close()
        print("Browser closed")

if __name__ == "__main__":
    # Prompt the user for the search query
    query = input("Enter the search query: ")
    
    # Run the search
    google_search(query)