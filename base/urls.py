from django.urls import include, path
from . import views
from .views import create_watchlist, get_tracked_products, search_product, add_tracked_product  # Explicit imports for clarity
from rest_framework.routers import DefaultRouter

# Set up router
router = DefaultRouter()

urlpatterns = [
    path('', views.index, name='index'),  # Root endpoint
    path('register', views.register, name='register'),  # User registration
    path('login', views.MyTokenObtainPairView.as_view(), name='login'),  # JWT login
    path('logout', views.user_logout, name='logout'),  # User logout
    path('search/', search_product, name='search'),  # Search products endpoint
    path('add-tracked-product/', add_tracked_product, name='add-tracked-product'),  # Add product to tracked list
    path('get-tracked-products/', get_tracked_products, name='get-tracked-products'),
    path('create-watchlist/', create_watchlist, name='create-watchlist'),
    path('get-user-watchlists/', views.get_user_watchlists, name='get-user-watchlists'),
    path('add-products-to-watchlist/', views.add_products_to_watchlist, name='add-products-to-watchlist'),
    path('delete-watchlist/<int:watchlist_id>/', views.delete_watchlist, name='delete-watchlist'),
    path('change-watchlist-name/<int:watchlist_id>/', views.change_watchlist_name, name='change-watchlist-name'),
    path('remove-product-from-watchlist/<int:watchlist_id>/<int:product_id>/', views.remove_product_from_watchlist, name='remove-product-from-watchlist'),
    path('', include(router.urls)),  # Include router-generated URLs (if any future view sets are added)
]
