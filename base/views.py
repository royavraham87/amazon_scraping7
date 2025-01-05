from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from .serializers import ProductSerializer, SearchResultSerializer, TrackedProductSerializer, WatchlistSerializer
from .models import Product, SearchResult, TrackedProduct, Watchlist
from rest_framework import viewsets
from scraper.playwright_scraper import scrape_amazon  # Import the real scraper function
from asgiref.sync import async_to_sync  # To run async function synchronously
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import AccessToken

# ViewSets
class SearchResultViewSet(viewsets.ModelViewSet):
    queryset = SearchResult.objects.all()
    serializer_class = SearchResultSerializer

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Product.objects.filter(user=user)
        return Product.objects.none()

class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Watchlist.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['GET'])
def index(req):
    return Response('hello')

@api_view(['GET', 'POST'])
def custom_login(request):
    if request.method == 'GET':
        return Response({"message": "Please use POST to log in."})
    view = MyTokenObtainPairView.as_view()
    return view(request)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

@api_view(['POST'])
def user_logout(request):
    logout(request)
    access_token = request.headers.get('Authorization')
    if access_token:
        try:
            if access_token.startswith("Bearer "):
                access_token = access_token.split(" ")[1]
            AccessToken(access_token)  # Validate token
        except Exception as e:
            print(f"Error invalidating access token: {e}")
    return Response({"message": "Successfully logged out."}, status=200)

@api_view(['GET', 'POST'])
def register(request):
    if request.method == 'GET':
        return Response({"message": "Please use POST to register a new user."})
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    if not username or not email or not password:
        return Response({"error": "All fields (username, email, and password) are required"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=400)
    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_active = True
    user.is_staff = False
    user.save()
    return Response("New user registered successfully")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    user = request.user
    return Response({
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    })

@api_view(['GET'])
@permission_classes([])  # Open to all users
def search_product(request):
    query = request.query_params.get('query')
    if not query:
        return Response({"error": "Query parameter is required."}, status=400)

    user = request.user if request.user.is_authenticated else None
    user_id = user.id if user else None

    # Default to superuser "roya" if no authenticated user
    if not user_id:
        try:
            superuser = User.objects.filter(is_superuser=True, username="roya").first()
            if not superuser:
                return Response({"error": "Superuser 'roya' not found. Please create a superuser named 'roya'."}, status=500)
            user_id = superuser.id
        except Exception as e:
            return Response({"error": f"An error occurred while setting default user: {str(e)}"}, status=500)

    try:
        # Trigger the scraper (no need to return scraped products in JSON response)
        async_to_sync(scrape_amazon)(query, user_id)

        # Response indicating success
        return Response({
            "message": f"Search for '{query}' completed successfully"
        }, status=200)
    except Exception as e:
        print(f"Error during scraping: {e}")
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_tracked_product(request):
    user = request.user
    product_name = request.data.get('product_name')

    if not product_name:
        return Response({"error": "Product name is required."}, status=400)

    try:
        # Check if the product is already being tracked
        product = TrackedProduct.objects.filter(title=product_name, user=user).first()
        if product:
            return Response({"message": f"Product '{product.title}' is already being tracked."}, status=400)

        # Adjust the current time to GMT+2
        current_time_gmt2 = (timezone.now() + timedelta(hours=2)).replace(microsecond=0)

        # Create the new tracked product
        new_product = TrackedProduct.objects.create(
            user=user,
            title=product_name,
            price=request.data.get('price'),  # Should be passed as a valid Decimal or None
            rating=request.data.get('rating'),
            reviews=request.data.get('reviews'),
            availability=request.data.get('availability'),
            date_scraped=current_time_gmt2
        )

        return Response({"message": f"Product '{new_product.title}' added to your tracked products."}, status=201)
    except Exception as e:
        print(f"Error adding tracked product: {e}")
        return Response({"error": f"An issue occurred: {str(e)}"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tracked_products(request):
    """
    Fetch the tracked products for the logged-in user.
    """
    user = request.user
    try:
        # Retrieve products tracked by the logged-in user
        tracked_products = TrackedProduct.objects.filter(user=user)

        # Include the product ID in the serialized data
        data = [
            {
                "id": product.id,
                "user": product.user.username,
                "title": product.title,
                "price": float(product.price) if product.price else None,  # Convert Decimal to float for API response
                "rating": product.rating,
                "reviews": product.reviews,
                "availability": product.availability,
                "date_scraped": product.date_scraped,
            }
            for product in tracked_products
        ]

        return Response(data, status=200)
    except Exception as e:
        print(f"Error fetching tracked products: {e}")
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)

    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_watchlist(request):
    """
    Create a new watchlist for the authenticated user.
    """
    user = request.user
    watchlist_name = request.data.get('name')  # User provides the name for the watchlist

    # Validate the watchlist name
    if not watchlist_name:
        return Response({"error": "Watchlist name is required."}, status=400)
    if len(watchlist_name) < 3:
        return Response({"error": "Watchlist name must be at least 3 characters long."}, status=400)

    try:
        # Check if a watchlist with the same name already exists for this user
        if Watchlist.objects.filter(user=user, name=watchlist_name).exists():
            return Response(
                {"error": f"A watchlist named '{watchlist_name}' already exists for the user."},
                status=400
            )

        # Create a new watchlist for the user
        watchlist = Watchlist.objects.create(user=user, name=watchlist_name)

        # Debugging: Log the created watchlist
        print(f"Created Watchlist: {watchlist}")

        return Response(
            {"message": f"Watchlist '{watchlist_name}' created successfully."},
            status=201
        )

    except Exception as e:
        # Handle unexpected errors
        print(f"Error creating watchlist: {e}")
        return Response(
            {"error": "An unexpected error occurred while creating the watchlist."},
            status=500
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_watchlists(request):
    """
    Retrieve all watchlists for the logged-in user, including the products in each watchlist.
    """
    user = request.user

    try:
        # Fetch all watchlists for the logged-in user
        watchlists = Watchlist.objects.filter(user=user).prefetch_related('products')

        if not watchlists.exists():
            return Response({"message": "No watchlists found for the user."}, status=404)

        # Serialize the watchlists along with their products
        serialized_watchlists = []
        for watchlist in watchlists:
            products = watchlist.products.all()
            product_details = [
                {
                    "id": product.id,
                    "title": product.title,
                    "price": float(product.price) if product.price else None,  # Convert Decimal to float
                    "rating": product.rating,
                    "reviews": product.reviews,
                    "availability": product.availability,
                    "date_scraped": product.date_scraped,
                }
                for product in products
            ]

            serialized_watchlists.append({
                "id": watchlist.id,
                "name": watchlist.name,
                "created_at": watchlist.created_at,
                "updated_at": watchlist.updated_at,
                "products_count": products.count(),
                "products": product_details  # Include product details in the response
            })

        return Response(serialized_watchlists, status=200)

    except Exception as e:
        print(f"Error retrieving user watchlists: {e}")
        return Response({"error": "An unexpected error occurred while fetching watchlists."}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_products_to_watchlist(request):
    """
    Add selected tracked products to a specific watchlist for the authenticated user.
    """
    user = request.user
    watchlist_id = request.data.get('watchlist_id')
    product_ids = request.data.get('product_ids', [])

    # Validate inputs
    if not watchlist_id:
        return Response({"error": "Watchlist ID is required."}, status=400)
    if not product_ids:
        return Response({"error": "At least one product ID is required."}, status=400)

    try:
        # Validate the watchlist
        watchlist = Watchlist.objects.filter(id=watchlist_id, user=user).first()
        if not watchlist:
            return Response({"error": "Invalid watchlist ID or you do not own this watchlist."}, status=404)

        # Validate and filter the products
        products = TrackedProduct.objects.filter(id__in=product_ids, user=user)
        if len(products) != len(product_ids):
            return Response({"error": "Some product IDs are invalid or do not belong to you."}, status=400)

        # Add products to the watchlist
        for product in products:
            watchlist.products.add(product)

        # Save the changes and return success
        watchlist.save()
        return Response({"message": f"{len(products)} products successfully added to watchlist '{watchlist.name}'."}, status=200)

    except Exception as e:
        print(f"Error adding products to watchlist: {e}")
        return Response({"error": "An unexpected error occurred."}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_watchlist(request, watchlist_id):
    """
    Delete a watchlist by its ID for the authenticated user.
    """
    user = request.user
    try:
        # Fetch the watchlist for the current user
        watchlist = Watchlist.objects.filter(id=watchlist_id, user=user).first()
        if not watchlist:
            return Response({"error": "Watchlist not found or does not belong to you."}, status=404)

        # Delete the watchlist
        watchlist.delete()
        return Response({"message": f"Watchlist '{watchlist.name}' has been deleted."}, status=200)
    except Exception as e:
        print(f"Error deleting watchlist: {e}")
        return Response({"error": "An unexpected error occurred while deleting the watchlist."}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_watchlist_name(request, watchlist_id):
    """
    Update the name of a watchlist for the authenticated user.
    """
    user = request.user
    new_name = request.data.get('name')

    if not new_name:
        return Response({"error": "New watchlist name is required."}, status=400)

    try:
        # Fetch the watchlist for the current user
        watchlist = Watchlist.objects.filter(id=watchlist_id, user=user).first()
        if not watchlist:
            return Response({"error": "Watchlist not found or does not belong to you."}, status=404)

        # Check if the new name already exists for the user
        if Watchlist.objects.filter(user=user, name=new_name).exists():
            return Response({"error": "A watchlist with this name already exists."}, status=400)

        # Update the watchlist name
        watchlist.name = new_name
        watchlist.save()
        return Response({"message": f"Watchlist name has been updated to '{new_name}'."}, status=200)
    except Exception as e:
        print(f"Error updating watchlist name: {e}")
        return Response({"error": "An unexpected error occurred while updating the watchlist name."}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_product_from_watchlist(request, watchlist_id, product_id):
    """
    Remove a product from a user's watchlist.
    """
    user = request.user

    try:
        # Fetch the watchlist
        watchlist = Watchlist.objects.filter(id=watchlist_id, user=user).first()
        if not watchlist:
            return Response({"error": "Watchlist not found or does not belong to the user."}, status=404)

        # Fetch the product
        product = watchlist.products.filter(id=product_id).first()
        if not product:
            return Response({"error": "Product not found in the watchlist."}, status=404)

        # Remove the product from the watchlist
        watchlist.products.remove(product)

        # Debugging: Log the action
        print(f"Removed Product: {product.title} from Watchlist: {watchlist.name}")

        return Response(
            {"message": f"Product '{product.title}' removed from watchlist '{watchlist.name}' successfully."},
            status=200,
        )

    except Exception as e:
        print(f"Error removing product from watchlist: {e}")
        return Response(
            {"error": "An unexpected error occurred while removing the product from the watchlist."},
            status=500,
        )

