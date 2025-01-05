from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from decimal import Decimal, InvalidOperation


def current_time_gmt2():
    """Get the current time adjusted to GMT+2."""
    return (timezone.now() + timedelta(hours=2)).replace(microsecond=0)


class SearchResult(models.Model):
    query = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255)
    product_url = models.URLField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=current_time_gmt2)

    def __str__(self):
        return self.product_name


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    search_result = models.ForeignKey(SearchResult, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    created_at = models.DateTimeField(default=current_time_gmt2)

    def __str__(self):
        return self.search_result.product_name if self.search_result else "Unassociated Product"


class TrackedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    reviews = models.IntegerField(null=True, blank=True)
    availability = models.CharField(max_length=100, null=True, blank=True, default="Unknown")
    date_scraped = models.DateTimeField(default=current_time_gmt2)

    def __str__(self):
        return (
            f"Title: {self.title} | Price: {self.price} | Rating: {self.rating} | "
            f"Reviews: {self.reviews} | Availability: {self.availability} | Scraped on: {self.date_scraped} | "
            f"User: {self.user.username}"
        )


class PriceHistory(models.Model):
    product = models.ForeignKey(TrackedProduct, on_delete=models.CASCADE, related_name="price_history")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_numeric = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability = models.CharField(max_length=100, null=True, blank=True, default="Unknown")
    date_recorded = models.DateTimeField(default=current_time_gmt2)

    def save(self, *args, **kwargs):
        """
        Automatically populate price_numeric from price when saving.
        """
        if self.price and self.price_numeric is None:
            try:
                # Ensure the price is a valid Decimal and assign it directly to price_numeric
                self.price_numeric = Decimal(self.price)
            except (InvalidOperation, ValueError):
                print(f"Invalid price format for '{self.price}'. Unable to convert to numeric.")
                self.price_numeric = None
        elif not self.price and self.price_numeric:
            # If only price_numeric is provided, sync it back to the price field
            self.price = self.price_numeric
        elif self.price and self.price_numeric:
            # Ensure price and price_numeric are consistent
            try:
                price_as_decimal = Decimal(self.price)
                if price_as_decimal != self.price_numeric:
                    self.price_numeric = price_as_decimal
            except (InvalidOperation, ValueError):
                print(f"Mismatch in price and price_numeric for '{self.product}'. Resetting price_numeric.")
                self.price_numeric = None

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.product.title} - Price: {self.price} (Numeric: {self.price_numeric}) "
            f"- Availability: {self.availability} on {self.date_recorded}"
        )

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    products = models.ManyToManyField(TrackedProduct, related_name='watchlists')
    created_at = models.DateTimeField(default=current_time_gmt2)
    updated_at = models.DateTimeField(default=current_time_gmt2)

    def __str__(self):
        return f"{self.name} (Owner: {self.user.username})"
