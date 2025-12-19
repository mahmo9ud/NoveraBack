from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def WelcomePage(request):
    return HttpResponse("Welcome To My E-Commerce Clothing Store")