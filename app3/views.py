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
from bokeh.models import Toggle


def app3(request):
    return render(request,'app3.html')
#.........................................................................................................


def showtemp(request):
    
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    # Define path to NetCDF file (assuming 'nc' subfolder in static)

    netcdf_file_path = os.path.join(settings.BASE_DIR,  'app3', 'static', 'nc', 'Tmin.nc')
    netcdf_file_path1 = os.path.join(settings.BASE_DIR,  'app3', 'static', 'nc', 'Tmax.nc')

    # Read data from NetCDF file
    ds = xr.open_dataset(netcdf_file_path)
    ds1 = xr.open_dataset(netcdf_file_path1)
    valuearray = ds.TMP_2m
    valuearray1 = ds1.TMP_2m

    # Select data at specific latitude and longitude (e.g., Delhi coordinates)
    val = valuearray.sel(longitude=lng, latitude=lat, method='nearest')
    val1 = valuearray1.sel(longitude=lng, latitude=lat, method='nearest')


    # Convert data to a DataFrame
    df = val.to_dataframe()
    df1 = val1.to_dataframe()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Temp', x_axis_type='datetime', width=700)

    

    # Plot the time series data
    p.line(df.index, df['TMP_2m'], legend_label='Tmin', line_width=2, color="yellow")
    p.line(df1.index, df['TMP_2m'], legend_label='Tmax', line_width=0.5, color="green")

     # y2 = 3
    y2 = [3] * len(df)
    orange_line = p.line(df.index, y2, legend_label='Y2', line_width=0.5, color='orange', visible=False)

    # y1 = 1
    y1 = [1] * len(df)
    green_line = p.line(df.index, y1, legend_label='Y1', line_width=0.5, color='green', visible=False)

    # y3 = 5
    y3 = [5] * len(df)
    red_line = p.line(df.index, y3, legend_label='Y3', line_width=0.5, color='red', visible=False)

    # Create toggle buttons
    y2_toggle = Toggle(label="Y2", active=False, button_type="success")
    y1_toggle = Toggle(label="Y1", active=False, button_type="success")
    y3_toggle = Toggle(label="Y3", active=False, button_type="success")

    # Add callback to toggle visibility
    y2_toggle.js_link('active', orange_line, 'visible')
    y1_toggle.js_link('active', green_line, 'visible')
    y3_toggle.js_link('active', red_line, 'visible')

    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Wind Speed", "@y"),
    ], formatters={'@x': 'datetime'})
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
    script, div = components((p,y1_toggle,y2_toggle,y3_toggle))


    combined_script = "".join(script)
    combined_div = "".join(div)
    
    df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # Drop latitude and longitude columns
    df = df.drop(columns=['latitude', 'longitude'])

    # Convert data to CSV format
    csv_data = df.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        'csv_data': csv_data,
    }
    print(csv_data)
    
    return render(request, 'showtemp.html', context)