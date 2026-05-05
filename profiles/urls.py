from django.urls import path
from . import views

urlpatterns = [
    path('profiles/search', views.ProfileSearchView.as_view(), name='profiles-search'),
    path('profiles/export', views.ProfileExportView.as_view(), name='profiles-export'),

    path('profiles', views.ProfileListView.as_view(), name='profiles-list'),
    path('profiles/<uuid:profile_id>', views.ProfileDetailView.as_view(), name='profiles-detail'),
]
