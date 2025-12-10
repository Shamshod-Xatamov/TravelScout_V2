from django.urls import path
from . import views

urlpatterns = [
    path('', views.flight_search_page, name='flight_search'),
    path('api/search/', views.flight_search_api, name='flight_search_api'),
]