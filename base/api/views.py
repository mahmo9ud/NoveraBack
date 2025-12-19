from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from django.db import transaction
import time
from datetime import timedelta
import datetime
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count,F,Avg,Sum,Prefetch
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
