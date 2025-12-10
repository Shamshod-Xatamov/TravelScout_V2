from django.urls import path
from . import views

urlpatterns = [
    path('', views.stories_feed, name='stories_feed'),

    # Detail sahifa (UUID bilan)
    path('<uuid:uuid>/', views.story_detail, name='story_detail'),

    # API endpoints (Ichki ishlatish uchun ID qulay)
    path('api/create/', views.create_story, name='create_story'),
    path('api/like/<int:story_id>/', views.toggle_like, name='toggle_like'),
    path('api/save/<int:story_id>/', views.toggle_save, name='toggle_save'),
    path('api/comment/<int:story_id>/', views.add_comment, name='add_comment'),
    path('api/delete/<int:story_id>/', views.delete_story, name='delete_story'),
    path('api/share/<int:story_id>/', views.increment_share_count, name='increment_share'),
    path('api/edit/<int:story_id>/', views.edit_story, name='edit_story'),
]