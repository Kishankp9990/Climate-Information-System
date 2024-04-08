from django.shortcuts import render

# Create your views here.
#created by developer.
from django.http import HttpResponse
from django.db import connection
from django.http import JsonResponse
import json
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import HoverTool,TapTool,CustomJS
import pandas as pd
import os
import xarray as xr
from django.conf import settings
from django.templatetags.static import static


def app2(request):
    return render(request,'app2.html')
#.........................................................................................................


def showwindspeed(request):
    
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    # Define path to NetCDF file (assuming 'nc' subfolder in static)

    netcdf_file_path = os.path.join(settings.BASE_DIR,  'app2', 'static', 'nc', 'wind.nc')
    

    # Read data from NetCDF file
    ds = xr.open_dataset(netcdf_file_path)
    valuearray = ds.__xarray_dataarray_variable__

    # Select data at specific latitude and longitude (e.g., Delhi coordinates)
    val = valuearray.sel(lon=lng, lat=lat, method='nearest')

    # Convert data to a DataFrame
    df = val.to_dataframe()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Wind Speed', x_axis_type='datetime', width=1000)
    print(df.index)
    

    # Plot the time series data
    p.line(df.index, df['__xarray_dataarray_variable__'], legend_label='Wind Speed', line_width=2)


   # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Wind Speed", "@y"),
    ],formatters={'@x': 'datetime'})
    p.add_tools(hover)


    tap = TapTool()
    tap.callback = CustomJS(args=dict(hover=hover), code="""
        if (!hover.active) {
            hover.active = true;
        } else {
            hover.active = false;
        }
    """)
    p.add_tools(tap)

    # Convert the plot to HTML
    script, div = components(p)

    # Pass the script and div to the template
    context = {
        'script': script,
        'div': div,
    }
    
    return render(request, 'showwindspeed.html', context)