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
    # path('products/',views.get_all_products),
    # path('products/get/',views.get_product_info),
    
    # # Cart
    # path('cart/add/',views.add_item_to_cart),
    # path('cart/remove/',views.remove_item_from_cart),
    # path('cart/edit/',views.edit_cart),
    # path('cart/items/',views.show_cart_items),
    # path('cart/clear/',views.clear_cart),

    # # Order
    # path('order/add/',views.place_order),
    # path('order/cancel/',views.cancel_order),

    # # Wishlist
    # path('wishlist/add/',views.add_item_to_wishlist),
    # path('wishlist/remove/',views.remove_item_from_wishlist),
    # path('wishlist/items/',views.show_wishlist_items),

    # # Review
    # path('reviews/recent/',views.get_recent_reviews),
    # path('reviews/add/',views.add_review),

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