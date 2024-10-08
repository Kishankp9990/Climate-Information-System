"""
URL configuration for CIS project.

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
from django.urls import path, include


admin.site.site_header = "Admin Login"
admin.site.site_title = "Portal"
admin.site.index_title = "Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path('',include('cisapp.urls')),
    path('basic/',include('cisapp.urls')),
    path('about/',include('cisapp.urls')),
    path('services/',include('cisapp.urls')),
    path('data/',include('cisapp.urls')),
    path('login/',include('cisapp.urls')),
    path('signup/',include('cisapp.urls')),
    path('apps/',include('cisapp.urls')),
    path('side/',include('cisapp.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('location_wise/',include('cisapp.urls')),
    path('shapefile/',include('cisapp.urls')),
    path('district_wise/',include('cisapp.urls')),
    path('river_basin/',include('cisapp.urls')),
    path('pptbasin/',include('cisapp.urls')),
    path('wsbasin/',include('cisapp.urls')),
    path('tempbasin/',include('cisapp.urls')),
    path('netcdf_handler/',include('cisapp.urls')),
    path('map/',include('cisapp.urls')),
    path('sf_db/',include('cisapp.urls')),
    path('dbTesting/',include('cisapp.urls')),
    path('sf_db_styling/',include('cisapp.urls')),
    path('plotting/',include('cisapp.urls')),
    path('aSync/',include('cisapp.urls')),
    path('bokeh/',include('cisapp.urls')),
    path('timeSeriesData/',include('cisapp.urls')),
    path('sfppt/',include('cisapp.urls')),
    path('delineation/',include('cisapp.urls')),
    path('sfws/',include('cisapp.urls')),
    path('sftemp/',include('cisapp.urls')),
    path('side-by-side/',include('cisapp.urls')),
    path('app1/',include('app1.urls')),
    path('showPrecipitation/',include('app1.urls')),
    path('app2/',include('app2.urls')),
    path('showwindspeed/',include('app2.urls')),
    path('app3/',include('app3.urls')),
    path('showtemp/',include('app3.urls')),


]
