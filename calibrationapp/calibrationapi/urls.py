"""
URL configuration for calibrationapi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.views.generic import TemplateView
from calibration_app.views import DashboardView, DisciplineBuilderView, ProgressTrackerView, RewardsTrackerView, AdminHubView
from calibration_app.socialview import MessageView, CommunityView, BuddiesView, UserSettingsView, UserProfileView


urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("calibration_app.auth_urls")),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('disciplinebuilder/', DisciplineBuilderView.as_view(), name='disciplinebuilder'),
    path('progresstracker/', ProgressTrackerView.as_view(), name='progresstracker'),
    path('rewards/', RewardsTrackerView.as_view(), name='rewards'),
    path('admin-hub/', AdminHubView.as_view(), name='admin_hub'),
    path('community/', CommunityView.as_view(), name='community'),
    path('messages/', MessageView.as_view(), name='messages'),
    path('buddies/', BuddiesView.as_view(), name='buddies'),
    path('settings/', UserSettingsView.as_view(), name='user_settings'),
    path('profile/', UserProfileView.as_view(), name= 'user_profile'),
    path('', TemplateView.as_view(template_name="index.html"), name='home'),
    path('app/', include('calibration_app.urls')),



]
