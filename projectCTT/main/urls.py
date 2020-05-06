from django.contrib import admin
from django.urls import path, include
from . import views



urlpatterns = [
	path('', views.MapView, name="MapView"),
	path('heatmap/', views.HeatMap, name="HeatMap"),
]
















