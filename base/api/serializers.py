from rest_framework import serializers
from base import models

class GetAllProductListSerializer(serializers.ModelSerializer):
    # We will calculate these in the View using SQL annotations for speed
    lowest_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = models.Product
        fields = [
            'id', 
            'name', 
            'category_name', 
            'lowest_price', # e.g., "From $10.00"
            'average_rating', 
            'review_count',
            'thumbnail', 
            'created_at'
        ]

    def get_thumbnail(self, obj):
        # Efficiently grab the first image from the pre-fetched variants
        # logic: Get first variant -> Get first image of that variant
        first_variant = next(iter(obj.variants.all()), None)
        if first_variant:
            first_image = next(iter(first_variant.images.all()), None)
            if first_image and first_image.img:
                return first_image.img.url 
        return None # Return placeholder URL if needed

# ... existing imports ...

class VariantSerializer(serializers.ModelSerializer):
    # Flatten the image URL list for the frontend
    images = serializers.SerializerMethodField()

    class Meta:
        model = models.ProductVariant
        fields = ['id', 'color_name', 'color_hex', 'size', 'price', 
                  'compare_at_price', 'stock', 'images', 'is_on_sale']

    def get_images(self, obj):
        # Returns a list of URLs: ["cloud/img1.jpg", "cloud/img2.jpg"]
        return [img.img.url for img in obj.images.all() if img.img]

class ProductDetailSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)
    category = serializers.CharField(source='category.name')
    
    # Aggregate data for the main header
    rating = serializers.FloatField(source='average_rating_value', read_only=True)

    class Meta:
        model = models.Product
        fields = [
            'id', 'name', 'description', 'category', 'material_composition', 
            'variants', 'rating', 'created_at'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    # We use the VariantSerializer to show full details (size, color, image)
    variant = VariantSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = models.CartItem
        fields = ['id', 'variant', 'quantity', 'price', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = models.Cart
        fields = ['id', 'items', 'total_price', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source='variant.product.name', read_only=True)
    
    class Meta:
        model = models.OrderItem
        fields = ['variant_name', 'quantity', 'price', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = models.Order
        fields = ['id', 'status', 'total_price', 'created_at', 'items', 
                  'full_name', 'full_address', 'phone_number', 'country']
        read_only_fields = ['id', 'status', 'total_price', 'created_at', 'items']

class CreateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = ['full_name', 'full_address', 'phone_number', 'country', 'order_notes']

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)

    class Meta:
        model = models.Review
        fields = ['id', 'customer_name', 'rating', 'comment', 'created_at']

class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Review
        fields = ['product', 'rating', 'comment']

    def validate(self, data):
        # Unique check is enforced at DB level, but good to validate here too
        request = self.context.get('request')
        if models.Review.objects.filter(customer=request.user, product=data['product']).exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        return data

class WishlistSerializer(serializers.ModelSerializer):
    # We reuse the list serializer so the wishlist looks just like the shop page
    products = GetAllProductListSerializer(many=True, read_only=True)

    class Meta:
        model = models.WishList
        fields = ['products']

