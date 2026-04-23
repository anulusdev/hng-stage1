from django.urls import path
from . import views

urlpatterns = [
    path('profiles/search', views.ProfileSearchView.as_view(), name='profiles-search'),
    path('profiles', views.ProfileListView.as_view(), name='profiles-list'),
    path('profiles/<str:profile_id>', views.ProfileDetailView.as_view(), name='profiles-detail'),
]