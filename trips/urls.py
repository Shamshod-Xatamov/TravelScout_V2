# trips/urls.py
from django.urls import path
from .views import (
    HomeView, TripCreateView, TripListView, TripDetailView,
    SignUpView, delete_trip, toggle_favorite,
    share_trip_options, public_trip_detail, profile_edit,
    ajax_password_change  # <--- MANA SHULARNI QO'SHDIM
)

urlpatterns = [
    # Asosiy sahifalar
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('dashboard/', TripListView.as_view(), name='my_plans_list'),

    # Create & Detail
    path('trip/new/', TripCreateView.as_view(), name='trip_new'),
    path('trip/<int:pk>/', TripDetailView.as_view(), name='trip_detail'),

    # DELETE (Page)
    path('trip/<int:pk>/delete/', delete_trip, name='delete_trip'),

    # SHARE PAGE (User kirib linkni copy qiladigan joy)
    path('trip/<int:pk>/share-page/', share_trip_options, name='trip_share_options'),

    # PUBLIC LINK (Do'stiga yuborganda ochiladigan link - UUID bilan)
    path('share/<uuid:share_uuid>/', public_trip_detail, name='trip_share'),

    # LIKE (AJAX funksiya)
    path('trip/<int:pk>/like/', toggle_favorite, name='toggle_favorite'),
    path('profile/', profile_edit, name='profile_edit'),

    path('change-my-password/', ajax_password_change, name='custom_password_change'),


]