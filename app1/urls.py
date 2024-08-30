#created by me
from django.urls import path
from .import views



urlpatterns = [
    path("",views.app1,name='app1'),
    path('showPrecipitation/',views.showPrecipitation,name='showPrecipitation'),
    
]
