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
from bokeh.layouts import column, row
from bokeh.themes import Theme
from bokeh.io import  curdoc
import pandas as pd
import os
import xarray as xr
from django.conf import settings
from django.templatetags.static import static
from bokeh.models import Toggle




def app1(request):
    return render(request,'app1.html')
#.........................................................................................................

def showPrecipitation(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path = '/home/kishan/datahub/meteorology/IMD/pr.nc'
    netcdf_file_path1 ='/home/kishan/datahub/climate/GCM_DS/EM_imd/historical/pr_1979_2014.nc'
    netcdf_file_path2 ='/home/kishan/datahub/climate/GCM_DS/EM/ssp245_pr/pr_2015_2100.nc'
    netcdf_file_path3 ='/home/kishan/datahub/climate/GCM_DS/EM/ssp545_pr/pr_2015_2100.nc'
    

    # Load the datasets
    ds = xr.open_dataset(netcdf_file_path)
    ds1 = xr.open_dataset(netcdf_file_path1)
    ds2 = xr.open_dataset(netcdf_file_path2)
    ds3 = xr.open_dataset(netcdf_file_path3)
    # print(ds)
    # print('this file')
    # Optionally slice the time range
    ds = ds.sel(time=slice('1979', '2014'))

    # Print dataset details to confirm coordinate names
    # print(ds)

    # print("Coordinates of ds:", ds.coords)

    # Access the precipitation data
    valuearray = ds.pr
    valuearray1 = ds1.pr
    valuearray2 = ds2.pr
    valuearray3 = ds3.pr



    # Data selection using consistent coordinate names, adjust as per actual names in the dataset
    val = valuearray.sel(lat=lat, lon=lng, method='nearest').compute()
    val1 = valuearray1.sel(lat=lat, lon=lng, method='nearest').compute()  # Ensure correct coordinate names
    val2 = valuearray2.sel(lat=lat, lon=lng, method='nearest').compute()
    val3 = valuearray3.sel(lat=lat, lon=lng, method='nearest').compute()
    # val = ds.sel(lat=lat, lon=lng, method='nearest')
    # val1 = ds1.sel(lat=lat, lon=lng, method='nearest')#.compute()  # Ensure correct coordinate names
    # val2 = ds2.sel(lat=lat, lon=lng, method='nearest')#.compute()
    # val3 = ds3.sel(lat=lat, lon=lng, method='nearest')#.compute()


    # Resample and sum by year directly from xarray DataArray
    imd = val.resample(time='Y').sum()
    hist = val1.resample(time='Y').sum()
    ssp245 = val2.resample(time='Y').sum()
    ssp585 = val3.resample(time='Y').sum()

    # Convert to DataFrames
    df = imd.to_dataframe()
    df1 = hist.to_dataframe()
    df2 = ssp245.to_dataframe()
    df3 = ssp585.to_dataframe()


    # df = val.to_dataframe()
    # df1 = val1.to_dataframe()
    # df2 = val2.to_dataframe()
    # df3 = val3.to_dataframe()
    
    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(-20,0, 0, -265))
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    print(theme_path)
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)

    # Plot the time series data
    observed=p.line(df.index, df['pr'], legend_label='imd', line_width=2)
    hist_line=p.line(df1.index, df1['pr'], legend_label='hist', color='orange', line_width=2)
    ssp245_line=p.line(df2.index, df2['pr'], legend_label='ssp245',  color='red', line_width=2)
    ssp585_line=p.line(df3.index, df3['pr'], legend_label='ssp585',  color='green', line_width=2)


    # Create toggle buttons
    y4_toggle = Toggle(label="observed", active=True, button_type="success")
    y1_toggle = Toggle(label="hist", active=True, button_type="success")
    y2_toggle = Toggle(label="ssp245", active=True, button_type="success")
    y3_toggle = Toggle(label="ssp585", active=True, button_type="success")

    # Add callback to toggle visibility
    y1_toggle.js_link('active', hist_line, 'visible')
    y2_toggle.js_link('active', ssp245_line, 'visible')
    y3_toggle.js_link('active', ssp585_line, 'visible')
    y4_toggle.js_link('active', observed, 'visible')

    

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
    # script, div = components((p,y1_toggle,y2_toggle,y3_toggle))
    
    layout = row(y4_toggle, y2_toggle, y3_toggle, y1_toggle,margin=(30,0, 0, 0))

    # Convert the plot to HTML
    script, div = components((p,layout))

    combined_script = "".join(script)
    combined_div = "".join(div)




    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        
    }

    
    return render(request, 'showPrecipitation.html', context)



    
