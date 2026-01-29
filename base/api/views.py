from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from django.db import transaction
import time
from datetime import timedelta
import datetime
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count,F,Avg,Sum,Prefetch,Q,Min,Max
from rest_framework import status
from .permissions import UnAuthenticated
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAdminUser,IsAuthenticated,AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from base import models
from django.db import IntegrityError
from . import serializers
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from rest_framework.pagination import PageNumberPagination
from django.db import connection
from django.conf import settings
from django.http import JsonResponse

################################# Auth
@api_view(['POST'])
@permission_classes([UnAuthenticated])
def register(request):
    email = request.data.get('email').strip()
    password1 = request.data.get('password1').strip()
    password2 = request.data.get('password2').strip()
    full_name = request.data.get('full_name').strip()

    if password1 != password2:
        return Response({"error":"passwords doesn't match"},status=status.HTTP_400_BAD_REQUEST)
      

    if models.User.objects.filter(email=email).exists():
        return Response({"error":"Registeration failed,Try again"},status=status.HTTP_400_BAD_REQUEST)


    try:
        user = models.User.objects.create_user(
        full_name = full_name,
        email = email,
        password= password1,
        )

        return Response({"message":"user created"},status=status.HTTP_201_CREATED)
    
    except:
        return Response({"error":"error occurred try again"})

@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
    except Exception:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        "email": user.email,
        "is_admin": user.is_staff,
    })

##################################


### products
class ProductPagination(PageNumberPagination):
    page_size = 20  # Default items per page
    page_size_query_param = 'page_size' # Frontend can override: /products/?page_size=50
    max_page_size = 100

    
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_products(request):
    
    # 1. Start with the base optimized query (same as before)
    queryset = models.Product.objects.filter(is_active=True).annotate(
        lowest_price=Min('variants__price'),
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).select_related('category').prefetch_related(
        Prefetch('variants', queryset=models.ProductVariant.objects.prefetch_related('images'))
    )

    # 2. FILTERING LOGIC (Your Job)
    
    # A. Search (Name or Description)
    search_query = request.query_params.get('search', None)
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    # B. Category Filter
    category = request.query_params.get('category', None)
    if category:
        queryset = queryset.filter(category__name__iexact=category)

    # C. Price Range Filter (Tricky: filter on the *annotated* lowest_price)
    min_price = request.query_params.get('min_price', None)
    max_price = request.query_params.get('max_price', None)

    if min_price:
        queryset = queryset.filter(lowest_price__gte=min_price)
    if max_price:
        queryset = queryset.filter(lowest_price__lte=max_price)

    # 3. Apply Pagination (Must happen AFTER filtering)
    paginator = ProductPagination()
    result_page = paginator.paginate_queryset(queryset, request)
    
    serializer = serializers.GetAllProductListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_detail(request, pk):
    try:
        # Optimized query: Fetch Product + Variants + Images in 1 go
        product = models.Product.objects.prefetch_related(
            Prefetch('variants', queryset=models.ProductVariant.objects.prefetch_related('images'))
        ).get(pk=pk, is_active=True)

        serializer = serializers.ProductDetailSerializer(product)
        return Response(serializer.data)

    except models.Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)
###





############################# Cart

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    """Get the current user's cart or create one if it doesn't exist."""
    cart, created = models.Cart.objects.get_or_create(customer=request.user)
    serializer = serializers.CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """
    Expects: { "variant_id": 12, "quantity": 1 }
    """
    variant_id = request.data.get('variant_id')
    quantity = int(request.data.get('quantity', 1))

    # 1. Get User's Cart
    cart, _ = models.Cart.objects.get_or_create(customer=request.user)

    # 2. Check Variant existence and Stock
    variant = get_object_or_404(models.ProductVariant, id=variant_id)
    if variant.stock < quantity:
        return Response({"error": "Not enough stock available"}, status=400)

    # 3. Update or Create Cart Item
    cart_item, created = models.CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={'price': variant.price} # Sets price on creation
    )

    if not created:
        # If item exists, add to quantity
        cart_item.quantity += quantity
        cart_item.save() # The model's save() method will update the price if needed
    else:
        # If new, manually set quantity (defaults used 1, but user might send more)
        cart_item.quantity = quantity
        cart_item.save()

    return Response(serializers.CartSerializer(cart).data, status=200)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """
    Update quantity of a specific item in the cart.
    Expects: { "quantity": 3 }
    """
    cart_item = get_object_or_404(models.CartItem, id=item_id, cart__customer=request.user)
    new_quantity = int(request.data.get('quantity', 1))

    if new_quantity < 1:
        cart_item.delete()
        return Response({"message": "Item removed"}, status=200)

    if cart_item.variant.stock < new_quantity:
        return Response({"error": "Exceeds available stock"}, status=400)

    cart_item.quantity = new_quantity
    cart_item.save()
    
    # Return the updated Cart to refresh frontend
    return Response(serializers.CartSerializer(cart_item.cart).data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(models.CartItem, id=item_id, cart__customer=request.user)
    cart_item.delete()
    
    # Return updated cart
    cart = models.Cart.objects.get(customer=request.user)
    return Response(serializers.CartSerializer(cart).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    cart = get_object_or_404(models.Cart, customer=request.user)
    cart.items.all().delete()
    return Response({"message": "All items removed from cart"}, 
        status=status.HTTP_204_NO_CONTENT)



#############################

