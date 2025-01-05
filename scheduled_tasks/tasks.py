from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import is_naive, make_aware
from django.core.mail import send_mail
from base.models import Watchlist, PriceHistory, TrackedProduct
from scraper.playwright_scraper import scrape_amazon
from decimal import Decimal, InvalidOperation
from rapidfuzz import fuzz
from .sale_events import sale_events
from asgiref.sync import async_to_sync

def is_sale_event(current_time):
    """
    Helper function to check if the current time falls within any sale event.
    """
    return any(start <= current_time <= end for start, end in sale_events)

@shared_task
def scheduled_scraping():
    """
    Scheduled scraping task that:
    - Scrapes watchlists periodically (e.g., every 7 days) if the product hasn't been scraped recently.
    - Scrapes during hardcoded sale events.
    - Matches product names with scraping results to ensure accuracy.
    """

    # Current local time (GMT+2) without milliseconds
    current_time = (timezone.now() + timedelta(hours=2)).replace(microsecond=0)

    # Fetch all watchlists
    watchlists = Watchlist.objects.prefetch_related('products').all()

    for watchlist in watchlists:
        print(f"Processing watchlist: {watchlist.name} (User: {watchlist.user.username})")

        # Loop through all products in the watchlist
        for tracked_product in watchlist.products.all():
            try:
                # Ensure `date_scraped` is timezone-aware and without milliseconds
                if tracked_product.date_scraped:
                    if is_naive(tracked_product.date_scraped):
                        tracked_product.date_scraped = make_aware(tracked_product.date_scraped)
                    tracked_product.date_scraped = tracked_product.date_scraped.replace(microsecond=0)

                # Check if the product was scraped during the current sale event
                # if is_sale_event(current_time):
                #     if tracked_product.date_scraped and tracked_product.date_scraped >= current_time - timedelta(days=7):
                #         print(f"Skipping product '{tracked_product.title}'; already scraped during this sale event.")
                #         continue
                #     print(f"Scraping product '{tracked_product.title}' during the sale event.")
                #     scrape_and_process(tracked_product, watchlist.user.id)
                #     continue

                # Check if the product was scraped in the last 7 days (outside sale events)
                # if tracked_product.date_scraped and tracked_product.date_scraped >= current_time - timedelta(days=7):
                #     print(f"Skipping product '{tracked_product.title}'; recently scraped on {tracked_product.date_scraped}.")
                #     continue

                # Scrape the product (regular periodic scrape)
                print(f"Scraping product '{tracked_product.title}' (regular periodic scrape).")
                scrape_and_process(tracked_product, watchlist.user.id)

            except Exception as e:
                print(f"Error processing product '{tracked_product.title}' in watchlist '{watchlist.name}': {e}")

    print(f"Scheduled scraping completed at {current_time}")

def scrape_product(product, user_id):
    """
    Scrape product details from Amazon and return the scrape results.
    """
    try:
        return async_to_sync(scrape_amazon)(product.title,user_id=user_id,single_page=True,scheduled_scraping=True)
    except Exception as e:
        print(f"Error scraping product '{product.title}': {e}")
        return None

def match_and_update_product(product, scrape_results):
    """
    Match scraped results to the product, update tracked product and price history.
    """
    try:
        if not scrape_results:
            print(f"No scrape results found for product '{product.title}'")
            return

        best_match = None
        highest_score = 0

        for result in scrape_results:
            # Use product.title consistently for comparison
            db_title = product.title.strip()
            scraped_title = result.get('title', '').strip()

            # Debugging: Log the titles being compared
            print(f"Comparing DB title: '{db_title}' with Scraped title: '{scraped_title}'")

            # Calculate similarity score between product title and scraped result title
            similarity_score = fuzz.ratio(db_title, scraped_title)

            # Debugging: Log the similarity score
            print(f"Similarity score: {similarity_score}")

            if similarity_score > highest_score:
                highest_score = similarity_score
                best_match = result

            # Early exit: if a perfect match is found, stop checking further
            if highest_score == 100:
                print(f"Perfect match found: {scraped_title} with similarity score: {highest_score}")
                break

        # If a match is found with a high enough score, process the matched product
        if best_match and highest_score > 75:
            print(f"Matched Product: {best_match['title']} with similarity score: {highest_score}")

            # Extract and clean price
            price_str = best_match.get('price', '0').replace('$', '').replace(',', '').strip()
            price_numeric = None

            try:
                price_numeric = Decimal(price_str)  # Convert cleaned price string to Decimal
            except (InvalidOperation, ValueError):
                print(f"Invalid price '{price_str}' for product '{product.title}'. Skipping price update.")
                price_numeric = None

            # Update existing tracked product
            tracked_product = TrackedProduct.objects.filter(id=product.id).first()
            if tracked_product:
                tracked_product.price = price_numeric
                tracked_product.rating = best_match.get('rating')
                tracked_product.reviews = best_match.get('reviews')
                tracked_product.availability = best_match.get('availability', None)
                tracked_product.date_scraped = timezone.now()
                tracked_product.save()
                print(f"Updated tracked product: {tracked_product.title}")
            else:
                print(f"Error: Could not find tracked product with ID {product.id} for updating.")

            # Update PriceHistory and detect price drop
            if price_numeric is not None and price_numeric > 0:
                save_price_history(product, price_numeric, best_match.get('availability', None))
                if detect_price_drop(product, price_numeric):
                    send_price_drop_alert(product, price_numeric)  # Send email alert for price drop
        else:
            # Handle the case where no suitable match is found
            print(f"No suitable match found for product '{product.title}'. Moving to the next product.")

    except Exception as e:
        print(f"Error during matching and updating for product '{product.title}': {e}")


def scrape_and_process(product, user_id):
    """
    Combine scraping and matching/updating for a product.
    """
    print(f"Starting scrape and process for product: {product.title}")
    scrape_results = scrape_product(product, user_id)

    # Debugging: Log the scrape results
    if scrape_results:
        print(f"Scrape results for '{product.title}': {[result.get('title', 'No title') for result in scrape_results]}")
    else:
        print(f"No scrape results for '{product.title}'")

    match_and_update_product(product, scrape_results)


def save_price_history(product, price_numeric, availability):
    """
    Save the current price and availability to the PriceHistory table.
    """
    try:
        # Ensure price_numeric is valid
        if price_numeric is None or price_numeric <= 0:
            print(f"Price unavailable for '{product.title}'. Adding as 'Unavailable'.")
            PriceHistory.objects.create(
                product=product,
                price=None,  # Null price for unavailable entries
                price_numeric=None,  # No numeric value for unavailable prices
                availability=availability or "Unavailable",  # Default to 'Unavailable' if None
            )
            return

        # Save the valid price to PriceHistory
        PriceHistory.objects.create(
            product=product,
            price=price_numeric,  # Save as Decimal for consistency
            price_numeric=price_numeric,  # Save as a Decimal for numeric field
            availability=availability or "In Stock",  # Default to 'In Stock' if None
        )
        print(f"Price history updated for '{product.title}' with price {price_numeric}.")
    except Exception as e:
        print(f"Error saving price history for '{product.title}': {e}")


def detect_price_drop(product, current_price, threshold=30):
    """
    Detect if there is a price drop equal to or greater than the given threshold percentage.
    """
    if not current_price or current_price <= 0:
        print(f"Invalid current price for product '{product.title}': {current_price}")
        return False

    # Fetch the most recent price history
    previous_price_entry = PriceHistory.objects.filter(product=product).order_by('-date_recorded').first()

    if not previous_price_entry:
        print(f"No previous price history for product '{product.title}'. Cannot detect price drop.")
        return False

    if not previous_price_entry.price_numeric or previous_price_entry.price_numeric <= 0:
        print(f"Invalid previous price in history for product '{product.title}': {previous_price_entry.price_numeric}")
        return False

    try:
        # Ensure both prices are Decimal for arithmetic operations
        previous_price = Decimal(previous_price_entry.price_numeric)

        # Calculate price drop percentage
        price_drop_percentage = ((previous_price - current_price) / previous_price) * 100

        # Debugging: Log the price drop details
        print(f"Previous price: {previous_price}, Current price: {current_price}, Price drop: {price_drop_percentage:.2f}%")

        if price_drop_percentage >= threshold:
            print(f"Significant price drop detected for '{product.title}': {price_drop_percentage:.2f}%")
            return True  # Significant price drop detected
        else:
            print(f"No significant price drop for '{product.title}': {price_drop_percentage:.2f}%")
            return False
    except InvalidOperation as e:
        print(f"Error calculating price drop for '{product.title}': {e}")
        return False


def send_price_drop_alert(product, current_price):
    """
    Send an email alert to the user about a significant price drop.
    """
    try:
        subject = f"Price Alert: '{product.title}' has dropped in price!"
        message = (
            f"Good news! The price of '{product.title}' has dropped significantly.\n\n"
            f"Current Price: ${current_price}\n"
            f"Availability: {product.availability or 'Unavailable'}\n\n"
            f"Check it out now!"
        )
        recipient = [product.user.email]

        # Debugging: Log email sending details
        print(f"Sending email to {recipient} about '{product.title}' with price ${current_price}")

        send_mail(
            subject=subject,
            message=message,
            from_email="alerts@yourapp.com",
            recipient_list=recipient,
        )
        print(f"Email alert sent to {product.user.email} for product '{product.title}'.")
    except Exception as e:
        print(f"Error sending email alert for '{product.title}': {e}")
