import asyncio
from scraper.refinement_scraper import scrape_hardcoded_product
from rapidfuzz import fuzz
from .email_utils import send_notification_email

async def run_scraping():
    """
    Runs the scraping process using the refinement scraper.
    The scraper extracts all product data, including availability.
    Then, this function finds and highlights the best product match.
    """
    print("Running scraping process...")

    try:
        # Step 1: Scrape all product data (including availability)
        products_data = await scrape_hardcoded_product(persist_browser=True)  # Ensure browser persistence

        if not products_data:
            print("❌ No products were scraped. Check the scraper for issues.")
            return

        # Step 2: Identify the best match using similarity scoring
        search_query = "LUDOS Clamor 2 PRO Wired Earbuds"  # The hardcoded search query
        best_match = None
        best_score = 0

        print("\n📌 The Final Scraped Data (from the actions.py):")
        for idx, product in enumerate(products_data):
            try:
                title = product.get("title", "No title")
                similarity_score = fuzz.partial_ratio(search_query.lower(), title.lower()) if title else 0

                # Track the best match
                if similarity_score > best_score:
                    best_score = similarity_score
                    best_match = {**product, "similarity_score": similarity_score}

                # Print all products (numbered)
                print(f"\n🔹 Product {idx + 1}/{len(products_data)}:")
                print(f"  Title            : {title}")
                print(f"  Price            : {product.get('price', 'N/A')}")
                print(f"  Numeric Price    : {product.get('price_numeric', 'N/A')}")
                print(f"  Rating           : {product.get('rating', 'N/A')}")
                print(f"  Reviews          : {product.get('reviews', 'N/A')}")
                print(f"  Availability     : {product.get('availability', 'N/A')}")
                print(f"  URL              : {product.get('url', 'No URL')}")
                print(f"  Similarity Score : {similarity_score}%")

            except Exception as e:
                print(f"⚠️ Error displaying product {idx + 1}: {e}")

        # Step 3: Print the best match with clean field handling
        if best_match:
            print("\n🏆 Best Product Match:")
            fields_to_display = {
                "title": "Title",
                "price": "Price",
                "price_numeric": "Price Numeric",
                "rating": "Rating",
                "reviews": "Reviews",
                "availability": "Availability",
                "url": "URL",
                "similarity_score": "Similarity Score"
            }

            for key, display_label in fields_to_display.items():
                value = best_match.get(key, "N/A")
                if key == "similarity_score":
                    print(f"  {display_label:<17}: {value}%")
                else:
                    print(f"  {display_label:<17}: {value}")

            # ✅ Send mock email notification
            subject = "📉 Price Drop Alert!"
            message = f"{best_match['title']} price just dropped!"
            recipient_list = ["test@example.com"]  # Change later to real user email(s)

            send_notification_email(subject, message, recipient_list)

        else:
            print("\n❌ No best match found.")

        print("\n✅ Scraping process completed.")
        return products_data

    except Exception as e:
        print(f"❌ Error during scraping process: {e}")


if __name__ == "__main__":
    asyncio.run(run_scraping())
