from django.urls import path
from . import views

urlpatterns = [
    path('profiles', views.ProfileListView.as_view(), name='profiles-list'),
    path('profiles/', views.ProfileListView.as_view(), name='profile-list-slash'),
    path('profiles/<str:profile_id>', views.ProfileDetailView.as_view(), name='profiles-detail'),
    path('profiles/<str:profile_id>/', views.ProfileDetailView.as_view(), name='profile-detail-slash'),
]