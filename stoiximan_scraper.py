from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_match_odds(url):
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        
        # Αντί για match_title_el:
        # Π.χ. περιμένουμε απλά να φορτωθεί ο τίτλος του tab
        WebDriverWait(driver, 10).until(EC.title_contains("Άρης"))
        print("Page title:", driver.title)
        
        # Ψάχνουμε όλα τα blocks που περιλαμβάνουν τις αποδόσεις
        all_blocks = driver.find_elements(By.CSS_SELECTOR, 
            "div.markets div.tw-bg-white-snow.tw-text-n-13-steel")
        
        for block in all_blocks:
            try:
                # Παίρνουμε το όνομα της αγοράς, π.χ. "Τελικό Αποτέλεσμα"
                market_name_el = block.find_element(By.CSS_SELECTOR, 
                    "div.tw-self-center")
                market_name = market_name_el.text.strip()
                
                # Ψάχνουμε τα κουμπιά επιλογών (αποδόσεις)
                selections = block.find_elements(By.CSS_SELECTOR, 
                    "div.selections__selection")
                
                # Εκτυπώνουμε την “κεφαλίδα” της αγοράς
                print(f"\n[{market_name}]")
                
                for sel in selections:
                    # label: συνήθως στο span.selection-horizontal-button__title
                    label_el = sel.find_element(
                        By.CSS_SELECTOR, ".selection-horizontal-button__title"
                    )
                    label_text = label_el.text.strip()
                    
                    # απόδοση: συνήθως στο span.tw-text-s.tw-leading-s.tw-font-bold...
                    odd_el = sel.find_element(
                        By.CSS_SELECTOR, "span.tw-text-s.tw-leading-s.tw-font-bold"
                    )
                    odd_value = odd_el.text.strip()
                    
                    print(f" - {label_text}: {odd_value}")
                    
            except Exception as e:
                # Αν κάποιο block δεν έχει market name ή selections, απλώς το προσπερνάμε
                pass
        
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://www.stoiximan.gr/apodoseis/aris-aek/63686772/"
    scrape_match_odds(url)
