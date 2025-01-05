from django.utils.timezone import make_aware
from datetime import datetime

# Define hardcoded sale events for 2025 as timezone-aware (GMT+0)
sale_events = [
    (make_aware(datetime(2025, 1, 1)), make_aware(datetime(2025, 1, 7))),  # New Year’s Sale
    (make_aware(datetime(2025, 2, 1)), make_aware(datetime(2025, 2, 14))),  # Valentine’s Day Sale
    (make_aware(datetime(2025, 3, 20)), make_aware(datetime(2025, 4, 25))),  # Spring Event
    (make_aware(datetime(2025, 4, 1)), make_aware(datetime(2025, 4, 7))),  # Spring Event continues
    (make_aware(datetime(2025, 5, 1)), make_aware(datetime(2025, 5, 12))),  # Mother’s Day
    (make_aware(datetime(2025, 6, 15)), make_aware(datetime(2025, 6, 25))),  # Summer Sale
    (make_aware(datetime(2025, 7, 18)), make_aware(datetime(2025, 7, 23))),  # Prime Day
    (make_aware(datetime(2025, 8, 10)), make_aware(datetime(2025, 8, 20))),  # Back to School Sale
    (make_aware(datetime(2025, 10, 20)), make_aware(datetime(2025, 10, 30))),  # Early Holiday Deals pre-Black Friday
    (make_aware(datetime(2025, 11, 28)), make_aware(datetime(2025, 11, 28))),  # Black Friday
    (make_aware(datetime(2025, 12, 1)), make_aware(datetime(2025, 12, 1))),  # Cyber Monday
    (make_aware(datetime(2025, 12, 5)), make_aware(datetime(2025, 12, 18))),  # Holiday Sale
    (make_aware(datetime(2025, 12, 26)), make_aware(datetime(2025, 12, 26))),  # Boxing Day
]
