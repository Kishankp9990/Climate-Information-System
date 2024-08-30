#created by me
from django.urls import path
from .import views



urlpatterns = [
    path("",views.app3,name='app3'),
    path('showtemp/',views.showtemp,name='showtemp'),
    
]