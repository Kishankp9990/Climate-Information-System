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




def app1(request):
    return render(request,'app1.html')
#.........................................................................................................

def showPrecipitation(request):
    
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    # Define path to NetCDF file (assuming 'nc' subfolder in static)

    netcdf_file_path = os.path.join(settings.BASE_DIR,  'app1', 'static', 'nc', 'pcp_1979.nc')
    

    # Read data from NetCDF file
    ds = xr.open_dataset(netcdf_file_path)
    valuearray = ds.APCP_sfc

    # Select data at specific latitude and longitude (e.g., Delhi coordinates)
    val = valuearray.sel(longitude=lng, latitude=lat, method='nearest')

    # Convert data to a DataFrame
    df = val.to_dataframe()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=1000)
    
    

    # Plot the time series data
    p.line(df.index, df['APCP_sfc'], legend_label='PPT', line_width=2)


   # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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

    df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # Drop latitude and longitude columns
    df = df.drop(columns=['latitude', 'longitude'])

    # Convert data to CSV format
    csv_data = df.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': script,
        'div': div,
        'csv_data': csv_data,
    }
    print(csv_data)
    
    return render(request, 'showPrecipitation.html', context)



    
