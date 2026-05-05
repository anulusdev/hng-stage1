from django.urls import path
from . import views

urlpatterns = [
    path('github', views.GitHubLoginView.as_view(), name='github-login'),
    path('github/callback', views.GitHubCallbackView.as_view(), name='github-callback'),
    path('refresh', views.TokenRefreshView.as_view(), name='token-refresh'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('me', views.WhoAmIView.as_view(), name='whoami'),
]