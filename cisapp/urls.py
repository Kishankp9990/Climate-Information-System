#created by me
from django.urls import path
from .import views



urlpatterns = [
    path("",views.index,name='index'),
    path('basic',views.basic,name='basic'),
    path('location',views.location,name='location'),
    path('netcdf_handler',views.netcdf_handler,name='netcdf_handler'),
    path('map',views.map,name='map'),
    path('sf',views.sf,name='sf'),
    path('dbTesting',views.dbTesting,name='dbTesting'),
    path('sf_db_styling',views.sf_db_styling,name='sf_db_styling'),
    path('plotting',views.plotting,name='plotting'),
    path('sf_db',views.sf_db,name='sf_db'),
    path('aSync',views.aSync,name='aSync'),
    path('bokeh',views.bokeh,name='bokeh'),
    path('timeSeriesData',views.timeSeriesData,name='timeSeriesData')
]
