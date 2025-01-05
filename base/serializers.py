from rest_framework import serializers
from .models import Product, SearchResult, Watchlist, TrackedProduct, PriceHistory


class SearchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchResult
        fields = ['product_name', 'product_url', 'price', 'query', 'created_at']  # All fields included


class ProductSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Include user field for better context
    search_result = SearchResultSerializer()  # Serialize related search result

    class Meta:
        model = Product
        fields = ['id', 'user', 'created_at', 'price', 'search_result']  # Match field names in the model


class TrackedProductSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Include user field for context

    class Meta:
        model = TrackedProduct
        fields = ['user', 'title', 'price', 'rating', 'reviews', 'availability', 'date_scraped']  # Fields match the model
        extra_kwargs = {
            'price': {'max_digits': 10, 'decimal_places': 2},  # Reflect model's DecimalField attributes
            'rating': {'max_digits': 3, 'decimal_places': 1},  # Ensure consistency
        }


class PriceHistorySerializer(serializers.ModelSerializer):
    product = TrackedProductSerializer()  # Serialize the related tracked product

    class Meta:
        model = PriceHistory
        fields = ['product', 'price', 'price_numeric', 'availability', 'date_recorded']  # All fields included
        extra_kwargs = {
            'price': {'max_digits': 10, 'decimal_places': 2},  # Match model changes
            'price_numeric': {'max_digits': 10, 'decimal_places': 2},  # Reflect DecimalField
        }


class WatchlistSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Include user field for clarity
    products = TrackedProductSerializer(many=True, read_only=True)  # Show related products in the watchlist

    class Meta:
        model = Watchlist
        fields = ['id', 'user', 'name', 'products', 'created_at', 'updated_at']  # Include all necessary fields
        read_only_fields = ['user', 'created_at', 'updated_at']  # Ensure these fields cannot be updated
