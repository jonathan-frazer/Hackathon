from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.login_page, name="Login Page"),
    path('dashboard/', views.dashboard_page, name="Dashboard Page"),
    path('logout/',views.logout_page,name="Logout Page")
]