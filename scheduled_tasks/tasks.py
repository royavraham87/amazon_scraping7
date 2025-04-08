# tasks.py

import asyncio
from datetime import datetime
from django.utils.timezone import now
from .sale_events import sale_events
from scraper.refinement_scraper import scrape_hardcoded_product
from .email_utils import send_notification_email


def scheduled_scraping():
    """Main scheduled scraping logic, runs inside APScheduler."""
    print("\n⏰ Running scheduled scraping...")

    # ⬇️ Import models *inside* the function to avoid early access errors
    from base.models import TrackedProduct, PriceHistory

    def is_today_sale_event():
        """Check if today is a sale event."""
        today = now().date()
        return any(event_start.date() <= today <= event_end.date() for event_start, event_end in sale_events)

    def has_been_scraped_recently(product):
        """Check if product was scraped in the last 7 days."""
        latest_history = PriceHistory.objects.filter(product=product).order_by("-date_recorded").first()
        if not latest_history:
            return False
        days_since_scraped = (now() - latest_history.date_recorded).days
        return days_since_scraped <= 7

    is_sale_day = is_today_sale_event()
    products_to_scrape = []

    for product in TrackedProduct.objects.all():
        if is_sale_day or not has_been_scraped_recently(product):
            products_to_scrape.append(product)

    if not products_to_scrape:
        print("✅ No products need scraping today.")
        return

    print(f"🔍 Found {len(products_to_scrape)} product(s) to scrape.")
    asyncio.run(process_scraping(products_to_scrape))


async def process_scraping(products_to_scrape):
    """Async scraping and price comparison logic."""
    from base.models import PriceHistory  # safe inside async context

    for product in products_to_scrape:
        print(f"\n🔎 Scraping product: {product.title}")
        try:
            results = await scrape_hardcoded_product(persist_browser=False)
        except Exception as e:
            print(f"❌ Failed to scrape product: {e}")
            continue

        for result in results:
            if result["title"].lower() == product.title.lower():
                try:
                    new_price = result["price_numeric"]
                    old_entry = PriceHistory.objects.filter(product=product).order_by("-date_recorded").first()

                    if old_entry and old_entry.price_numeric:
                        old_price = old_entry.price_numeric
                        drop_percentage = ((old_price - new_price) / old_price) * 100

                        if drop_percentage >= 30:
                            subject = "📉 Price Drop Alert!"
                            message = f"{product.title} has dropped from ${old_price:.2f} to ${new_price:.2f}!"
                            recipient = [product.user.email]
                            send_notification_email(subject, message, recipient)
                except Exception as e:
                    print(f"⚠️ Error checking price drop: {e}")

    print("\n✅ Scheduled scraping finished.")
