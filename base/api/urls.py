from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('auth/me/',views.me),

    # Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/signup/',views.register),
    path('auth/logout/',views.logout),

    # # Product
    path('products/',views.get_all_products),
    path('products/<str:pk>/',views.get_product_detail),
    
    # path('products/get/',views.get_product_info),
    
    # # Cart
    path('cart/', views.get_cart, name='get_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    # # Order
    path('orders/place/', views.place_order, name='place_order'),
    path('orders/history/', views.get_my_orders, name='my_orders'),

    # # Wishlist
    path('wishlist/', views.get_wishlist, name='get_wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),

    path('reviews/add/', views.add_review, name='add_review'),
    path('products/<str:product_id>/reviews/', views.get_product_reviews, name='product_reviews'),

    # # Payment (Stripe)
    # path('payment/create-checkout-session/',views.create_checkout_session),
    # path('payment/stripe-webhook/',views.stripe_webhook),

    # # Dashboard
    # path('dashboard/totalsales/',views.get_total_sales),
    # path('dashboard/totalstock/',views.get_total_stock),
    # path('dashboard/orders/recent/',views.get_latest_orders),
    # path('dashboard/order/<str:pk>/',views.order_detail_action),
    # path('dashboard/orders/',views.get_all_orders_num),
    # path('dashboard/reviews/',views.get_all_reviews),
    # path('dashboard/products/add/',views.create_product),
    # path('dashboard/products/<str:pk>/',views.product_detail_action),
    # path('dashboard/products/',views.get_all_products_num),
    # path('dashboard/users/',views.get_all_users_num),

    # # Charts
    # path('charts/products/low/',views.get_low_chart_info),
    # path('charts/products/top-selling/',views.get_top_sales_chart_info),
    # path('charts/sales-orders/',views.get_sales_orders_chart),
]