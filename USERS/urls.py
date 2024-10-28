from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.main, name='main'),
	path('submit_visit_request/', views.submit_visit_request, name='submit_visit_request'),
    path('home-owner/', views.ownerLogin, name='ownerLogin'),
    path('owner_dashboard/', views.owner_dashboard, name='owner_dashboard'),
	path('check_property/', views.check_property, name='check_property'),
    path('ownerLogout/', views.ownerLogout, name='ownerLogout'),
    path('Secretary_login/', views.secretaryLogin, name='secretaryLogin'),
	path('secretaryLogout/', views.secretaryLogout, name='secretaryLogout'),
    path('Admin/', views.adminLogin, name='adminLogin'),
    path('adminLogout/', views.adminLogout, name='adminLogout'),
    path('register/', views.register, name='register'),
    path('ar/', views.ar_view, name='ar_view'),
	path('reset-password/', views.password_reset_request2, name='password_reset_request2'),
    path('reset-password/<str:token>/', views.password_reset_confirm2, name='password_reset_confirm2'),
    path('password_reset_complete/', views.password_reset_complete, name='password_reset_complete'),
]


