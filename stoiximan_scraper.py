import time
from selenium import webdriver
from selenium.webdriver.common.by import By

def open_arrows_and_scroll(url):
    driver = webdriver.Chrome()
    driver.get(url)

    # Δίνουμε λίγο χρόνο να φορτώσει η σελίδα
    time.sleep(3)

    # 1) Βρίσκουμε όλα τα arrow SVGs
    arrows = driver.find_elements(
        By.CSS_SELECTOR, 
        "svg.sb-arrow.tw-icon-xs.push-right.tw-icon.tw-fill-n-48-slate.dark\\:tw-fill-n-75-smokey.tw-cursor-pointer"
    )

    # 2) Κλικάρουμε κάθε βελάκι (π.χ. για να ανοίξει το αντίστοιχο accordion)
    for arrow in arrows:
        try:
            arrow.click()
            time.sleep(0.2)  # Μικρή καθυστέρηση μεταξύ των κλικ
        except:
            pass

    # 3) Στο τέλος κάνουμε scroll ως το κάτω μέρος της σελίδας
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Μένουμε λίγο για να δούμε το αποτέλεσμα
    time.sleep(3)

    driver.quit()

if __name__ == "__main__":
    url = "https://www.stoiximan.gr/apodoseis/aris-aek/63686772/"
    open_arrows_and_scroll(url)
