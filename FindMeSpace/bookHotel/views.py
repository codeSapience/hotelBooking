from django.shortcuts import render
from django.urls import reverse



def homepage(request):
    context = {}
    return render(request, 'bookHotel/index.html', context)