from django.urls import path
from . import views
from django.urls.conf import re_path

urlpatterns = [
    path('', views.index, name='index'),
    path('plan-actual/', views.plan_actual, name='plan-actual'),
    re_path(r'^proyeccion/(?P<pk>\d+)/$', views.proyeccion, name='proyeccion'),
    re_path(r'^resultado/(?P<pk>\d+)/(?P<pk2>\d+)/$', views.resultado, name='resultado'),
    path('puntaje/', views.puntaje, name='puntaje'),
]