
from django.db import models
from django.dispatch import receiver
import uuid
from cloudinary.models import CloudinaryField
from django.db.models.signals import pre_save,post_save,pre_delete,post_delete
from django.core.mail import send_mail
from dirtyfields import DirtyFieldsMixin
from django.db.models import Avg
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, password, **extra_fields)

class User(AbstractUser):
    username = None  # Removes username field
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)

    # LINK THE NEW MANAGER HERE
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.full_name
    

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name



###################
class Product(models.Model):
    # Core Identity
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    
    # Material & Care
    material_composition = models.CharField(max_length=255) # e.g., "100% Cotton"
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    # Relationship
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    
    # Specifics
    color_name = models.CharField(max_length=50) # e.g., "Midnight Blue"
    color_hex = models.CharField(max_length=7,null=True,blank=True)    # e.g., "#000080"
    size = models.CharField(max_length=20)      # e.g., "L" or "32/34"
    
    # Commerce
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Current Price (Selling Price)"
    )
    compare_at_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Original Price (MSRP)"
    )

    # ... stock fields ...
    stock = models.PositiveIntegerField(default=0)


    @property
    def is_on_sale(self):
        """Returns True if the item is discounted."""
        if self.compare_at_price and self.compare_at_price > self.price:
            return True
        return False

    @property
    def discount_percentage(self):
        """Calculates the % off for badges (e.g., '25% OFF')."""
        if self.is_on_sale:
            discount = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            return round(discount)
        return 0

    @property
    def savings_amount(self):
        """Returns the actual money saved (e.g., '$20.00')."""
        if self.is_on_sale:
            return self.compare_at_price - self.price
        return 0
    
    @property
    def average_rating_value(self):
        return self.reviews.aggregate(avg=Avg("rating"))["avg"] or 0
 
    def __str__(self):
        return f"{self.product.name} - {self.color_name} - {self.size}"
    
    class Meta:
        unique_together = ('product', 'color_name', 'size')


class ProductImage(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='images', on_delete=models.CASCADE)
    img = CloudinaryField("products/",null=True)
    
###################


class Review(models.Model):
    customer = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])  #1–5 stars
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "customer")  # one review per customer per product
        ordering = ["-created_at"]

    def __str__(self):
        return self.product.name
    

class WishList(models.Model):
    customer = models.ForeignKey(User,on_delete=models.CASCADE,related_name='wishlist')
    products = models.ManyToManyField(Product,related_name='wishlists',blank=True)

    def __str__(self):
        return self.customer.username




class Order(DirtyFieldsMixin,models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # Biling details
    full_name = models.CharField(max_length=200,null=True)
    full_address = models.CharField(max_length=300,null=True)
    order_notes = models.TextField(null=True)
    phone_number = models.CharField(max_length=25,null=True)
    country = models.CharField(max_length=100,null=True)

    @property
    def total_price(self):
        return sum(item.quantity * item.price for item in self.items.all())
    
    STATUS_CHOICES = [
    ("pending", "Pending"),
    ("paid", "Paid"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
 
    def __str__(self):
        return str(self.id)



class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    variant = models.ForeignKey(ProductVariant,on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8,decimal_places=2,blank=True)

    @property
    def subtotal(self): # for each item not whole order
        return self.quantity * self.price
    
    def save(self,*args,**kwargs):
        self.price = self.variant.price
        super().save(*args,**kwargs)

    def __str__(self):
        return self.variant.product.name        



class Payment(models.Model):
    customer = models.ForeignKey(User,on_delete=models.CASCADE,related_name='payments')
    order = models.OneToOneField(Order,on_delete=models.CASCADE,related_name='payment')
    amount = models.DecimalField(decimal_places=2,max_digits=10)

    METHOD_CHOICES = [
        ("credit_card","Credit Card"),
        ("debit_card","Debit Card"),
        ("cash","Cash"),
        ("paypal","PayPal"),
        ("bank_transfer","Bank Transfer"),
        ("stripe","Stripe")
    ]

    method = models.CharField(max_length=50,choices=METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add = True)
    updated = models.DateTimeField(auto_now = True)
    transaction_id = models.CharField(max_length=100, null=True, unique=True)

    def __str__(self):
        return self.customer.username if self.customer else "Guest Cart" 




class Cart(models.Model):
    customer = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return self.customer.username if self.customer else "Guest Cart"




class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8,decimal_places=2,blank=True)

    @property
    def subtotal(self): # for each item not whole cart
        return self.quantity * self.price
    
    def save(self,*args,**kwargs):
        self.price = self.variant.price
        
        super().save(*args,**kwargs)

    def __str__(self):
        return self.variant.product.name














####################### Signals ########################

##### Commented cuz it takes so much time and slows the web #####


# @receiver(post_save,sender=User)
# def user_post_save_receiver(sender,instance,created,*args,**kwargs):
#     if created:
#         send_mail(
#     subject="Welcome!",
#     message=f"Hey {instance.username} Thank you for signing up in our e-commerce website",
#     from_email= settings.DEFAULT_FROM_EMAIL,
#     recipient_list=[instance.email],
#     fail_silently=True,
# )
#     else:
#         print("You account information has been updated")


# @receiver(post_save,sender=Order)
# def order_post_save_receiver(sender,instance,created,*args,**kwargs):
#     if created:
#         send_mail(
#     subject="Your Order",
#     message=f"Hello {instance.customer.username}, we wanted to inform you that your order has been placed successfully",
#     from_email=settings.DEFAULT_FROM_EMAIL,
#     recipient_list=[instance.customer.email],
#     fail_silently=True,
#     )
    
#     else:
#         if "status" in instance.get_dirty_fields():
#             if instance.status == 'shipped':
#                 message = f"Hello {instance.customer.username}, you order has been shipped and will be delivered soon.\nStay Tuned"
#             elif instance.status == 'delivered':
#                 message = f"Hello {instance.customer.username}, you order has been delivered to your place"
#             elif instance.status == 'cancelled':
#                 message = f"Hello {instance.customer.username}, you order has been been cancelled"
#             elif instance.status == 'pending':
#                 message = f"Hello {instance.customer.username}, you order is now pending"
#             elif instance.status == 'paid':
#                 message = f"Hello {instance.customer.username}, you order has been paid successfully"
#             else:
#                 return
        
#         else:
#             return 
        
#         send_mail(
#     subject="Your Order",
#     message=message,
#     from_email=settings.DEFAULT_FROM_EMAIL,
#     recipient_list=[instance.customer.email],
#     fail_silently=True,
# )
