import requests
import pandas as pd
import time

from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin


# =====================================
# 1. WEBSITE CONFIGURATION
# =====================================

BASE_URL = "https://books.toscrape.com/"

headers = {
    "User-Agent": "Mozilla/5.0"
}


# =====================================
# 2. CREATE SESSION
# =====================================

session = requests.Session()
session.headers.update(headers)


# =====================================
# 3. RETRY CONFIGURATION
# =====================================

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://", adapter)

print("Scraper configured successfully!")


# =====================================
# 4. TEST WEBSITE CONNECTION
# =====================================

response = session.get(BASE_URL, timeout=15)

print("Status Code:", response.status_code)

if response.status_code == 200:
    print("Website connected successfully!")
else:
    print("Website connection failed!")
    raise SystemExit


# =====================================
# 5. SCRAPE BOOK INFORMATION
# =====================================

def scrape_books(url):

    response = session.get(url, timeout=15)
    response.raise_for_status()

    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")

    books = []

    book_containers = soup.find_all(
        "article",
        class_="product_pod"
    )

    for book in book_containers:

        title = book.h3.a["title"]

        price = book.find(
            "p",
            class_="price_color"
        ).text.replace("£", "").replace("Â", "")

        availability = book.find(
            "p",
            class_="instock availability"
        ).text.strip()

        rating = book.find(
            "p",
            class_="star-rating"
        )["class"][1]

        book_url = urljoin(
            url,
            book.h3.a["href"]
        )

        book_data = {
            "Title": title,
            "Price": float(price),
            "Rating": rating,
            "Availability": availability,
            "URL": book_url
        }

        books.append(book_data)

    next_button = soup.select_one("li.next a")

    if next_button:
        next_url = urljoin(
            url,
            next_button["href"]
        )
    else:
        next_url = None

    return books, next_url


# =====================================
# 6. SCRAPE ALL PAGES
# =====================================

all_books = []

current_url = BASE_URL
page_number = 1

while current_url:

    print(f"Scraping page {page_number}...")

    page_books, current_url = scrape_books(current_url)

    all_books.extend(page_books)

    page_number += 1

    if current_url:
        time.sleep(1)

print("\nTotal Books Scraped:", len(all_books))


# =====================================
# 7. CREATE DATAFRAME
# =====================================

df = pd.DataFrame(all_books)

print("\nFirst 5 Records:")
print(df.head())


# =====================================
# 8. SAVE CSV
# =====================================

df.to_csv(
    "books_data.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nCSV file created successfully!")


# =====================================
# 9. SAVE JSON
# =====================================

df.to_json(
    "books_data.json",
    orient="records",
    indent=4,
    force_ascii=False
)

print("JSON file created successfully!")


# =====================================
# 10. GENERATE ANALYTICAL REPORT
# =====================================

if not df.empty:

    total_books = len(df)

    average_price = df["Price"].mean()

    highest_price = df["Price"].max()

    lowest_price = df["Price"].min()

    rating_distribution = df["Rating"].value_counts()

    available_books = df[
        df["Availability"].str.contains(
            "In stock",
            case=False,
            na=False
        )
    ]

    report = f"""
========================================
       WEB SCRAPING ANALYTICAL REPORT
========================================

Total Books Scraped: {total_books}

Average Book Price: £{average_price:.2f}

Highest Book Price: £{highest_price:.2f}

Lowest Book Price: £{lowest_price:.2f}

Available Books: {len(available_books)}

Rating Distribution:

{rating_distribution.to_string()}

========================================
          SCRAPING COMPLETED
========================================
"""

    with open("report.txt", "w", encoding="utf-8") as file:
        file.write(report)

    print(report)

    print("Report generated successfully!")

else:

    print("No book data found!")


# =====================================
# 11. FINAL STATUS
# =====================================

print("\n================================")
print("WEB SCRAPING PIPELINE COMPLETED")
print("================================")

print("Generated Files:")
print("1. books_data.csv")
print("2. books_data.json")
print("3. report.txt")