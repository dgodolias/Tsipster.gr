from bs4 import BeautifulSoup

def parse_stoiximan_odds(html_file):
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Εντοπίζουμε όλα τα "blocks" αγορών.
    # Συνήθως έχουν class="tw-bg-white-snow tw-text-n-13-steel" μέσα σε div.markets
    all_blocks = soup.select("div.markets div.tw-bg-white-snow.tw-text-n-13-steel")

    for block in all_blocks:
        # Παίρνουμε το όνομα της αγοράς (π.χ. "Τελικό Αποτέλεσμα", "Draw No Bet" κ.λπ.)
        market_title_el = block.select_one("div.tw-self-center")
        if not market_title_el:
            continue

        market_name = market_title_el.get_text(strip=True)
        print(f"\n[{market_name}]")

        # Μέσα στο block, βρίσκουμε τα κουμπιά/επιλογές που περιέχουν αποδόσεις
        selections = block.select("div.selections__selection")

        for sel in selections:
            # Το label (π.χ. "1", "X", "2", "Ναι (GG)", κ.λπ.)
            label_el = sel.select_one(".selection-horizontal-button__title")
            # Η απόδοση (π.χ. "5.60", "1.62" κ.λπ.)
            odd_el = sel.select_one("span.tw-text-s.tw-leading-s.tw-font-bold")

            if label_el and odd_el:
                label = label_el.get_text(strip=True)
                odd   = odd_el.get_text(strip=True)
                print(f" - {label}: {odd}")

if __name__ == "__main__":
    parse_stoiximan_odds("stoiximan_final.html")
