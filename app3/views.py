from django.shortcuts import render

# Create your views here.
#created by developer.
from django.http import HttpResponse
from django.db import connection
from django.http import JsonResponse
import json
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import HoverTool,TapTool,CustomJS, InlineStyleSheet, Slider
from bokeh.layouts import column, row
import pandas as pd
import os
import xarray as xr
from django.conf import settings
from django.templatetags.static import static
from bokeh.models import Toggle
from bokeh.io import curdoc


def app3(request):
    return render(request,'app3.html')
#.........................................................................................................


def showtemp(request):
    
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    
    
    # Define path to NetCDF file (assuming 'nc' subfolder in static)

    netcdf_file_path = ('/home/kishan/datahub/meteorology/IMDAA/tmin/tmin_1979.nc')
    netcdf_file_path1 =('/home/kishan/datahub/meteorology/IMDAA/tmax/tmax_1979.nc')
    
    netcdf_file_path3 =('/home/kishan/datahub/climate/GCM_DS/EM/historical/tasmax_1979_2014.nc')
    netcdf_file_path4 =('/home/kishan/datahub/climate/GCM_DS/EM/historical/tasmin_1979_2014.nc')
    
    netcdf_file_path5 =('/home/kishan/datahub/climate/GCM_DS/EM/ssp245/tasmax_2015_2100.nc')
    netcdf_file_path6 =('/home/kishan/datahub/climate/GCM_DS/EM/ssp245/tasmin_2015_2100.nc')
    
    netcdf_file_path7 =('/home/kishan/datahub/climate/GCM_DS/EM/ssp585/tasmax_2015_2100.nc')
    netcdf_file_path8 =('/home/kishan/datahub/climate/GCM_DS/EM/ssp585/tasmin_2015_2100.nc')

    # Read data from NetCDF file
    ds = xr.open_dataset(netcdf_file_path)
    ds1 = xr.open_dataset(netcdf_file_path1)
    ds3 = xr.open_dataset(netcdf_file_path3)
    ds4 = xr.open_dataset(netcdf_file_path4)
    ds5 = xr.open_dataset(netcdf_file_path5)
    ds6 = xr.open_dataset(netcdf_file_path6)
    ds7 = xr.open_dataset(netcdf_file_path7)
    ds8 = xr.open_dataset(netcdf_file_path8)
    
    ds = ds.sel(time=slice('1979', '2014'))
    ds1 = ds1.sel(time=slice('1979', '2014'))
    
    valuearray = ds.TMP_2m
    valuearray1 = ds1.TMP_2m
    valuearray3 = ds3.tasmax
    valuearray4 = ds4.tasmin
    valuearray5 = ds5.tasmax
    valuearray6 = ds6.tasmin
    valuearray7 = ds7.tasmax
    valuearray8 = ds8.tasmin
    print(valuearray)

    # Select data at specific latitude and longitude (e.g., Delhi coordinates)
    val = valuearray.sel(longitude=lng, latitude=lat, method='nearest')
    val1 = valuearray1.sel(longitude=lng, latitude=lat, method='nearest')
    val3 = valuearray3.sel(lon=lng, lat=lat, method='nearest')
    val4 = valuearray4.sel(lon=lng, lat=lat, method='nearest')
    val5 = valuearray5.sel(lon=lng, lat=lat, method='nearest')
    val6 = valuearray6.sel(lon=lng, lat=lat, method='nearest')
    val7 = valuearray7.sel(lon=lng, lat=lat, method='nearest')
    val8 = valuearray8.sel(lon=lng, lat=lat, method='nearest')


    # Convert data to a DataFrame
    df = val.to_dataframe()
    df1 = val1.to_dataframe()
    df3 = val3.to_dataframe()
    df4 = val4.to_dataframe()
    df5 = val5.to_dataframe()
    df6 = val6.to_dataframe()
    df7 = val7.to_dataframe()
    df8 = val8.to_dataframe()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Temp', x_axis_type='datetime', width=700, margin=(-20,0, 0, -265))
    
    

    # Plot the time series data
    observed_min=p.line(df.index, df['TMP_2m'], legend_label='hist_Tmin', line_width=2, color="red",visible=False)
    observed_max=p.line(df1.index, df1['TMP_2m'], legend_label='hist_Tmax', line_width=0.5, color="red")
    hist_max=p.line(df3.index, df3['tasmax'], legend_label='hist_Tmax', line_width=2, color="green")
    hist_min=p.line(df4.index, df4['tasmin'], legend_label='hist_Tmin', line_width=0.5, color="green",visible=False)
    ssp245_max=p.line(df5.index, df5['tasmax'], legend_label='ssp245_Tmax', line_width=2, color="yellow")
    ssp245_min=p.line(df6.index, df6['tasmin'], legend_label='ssp245_Tmin', line_width=0.5, color="yellow",visible=False)
    ssp585_max=p.line(df7.index, df7['tasmax'], legend_label='ssp585_Tmax', line_width=2, color="blue")
    ssp585_min=p.line(df8.index, df8['tasmin'], legend_label='ssp585_Tmin', line_width=0.5, color="blue",visible=False)


    y5_toggle = Toggle(label="Show Min", active=False, button_type="success")
    y2_toggle = Toggle(label="hist", active=False, button_type="success")
    y1_toggle = Toggle(label="observed", active=False, button_type="success")
    y3_toggle = Toggle(label="ssp245", active=False, button_type="success")
    y4_toggle = Toggle(label="ssp585", active=False, button_type="success")
    # Add callback to toggle visibility for max/min
    y5_toggle_callback = CustomJS(args=dict(toggle5=y5_toggle,toggle4=y4_toggle,toggle3=y3_toggle,toggle2=y2_toggle,toggle1=y1_toggle,
        observed_min=observed_min, observed_max=observed_max,
        hist_min=hist_min, hist_max=hist_max,
        ssp245_min=ssp245_min, ssp245_max=ssp245_max,
        ssp585_min=ssp585_min, ssp585_max=ssp585_max
    ), code="""
        if (cb_obj.active) {
            toggle1.active=false;
            toggle2.active=false;
            toggle3.active=false;
            toggle4.active=false;
            toggle5.label="show max";
            observed_min.visible = true;
            observed_max.visible = false;
            hist_min.visible = true;
            hist_max.visible = false;
            ssp245_min.visible = true;
            ssp245_max.visible = false;
            ssp585_min.visible = true;
            ssp585_max.visible = false;
        }else{
            toggle1.active=true;
            toggle2.active=true;
            toggle3.active=true;
            toggle4.active=true;
            toggle5.label="show min";
            observed_min.visible = false;
            observed_max.visible = true;
            hist_min.visible = false;
            hist_max.visible = true;
            ssp245_min.visible = false;
            ssp245_max.visible = true;
            ssp585_min.visible = false;
            ssp585_max.visible = true;
            
        }
    """)



    


    # Add callback to toggle visibility
    y1_toggle_callback = CustomJS(args=dict(observed_min=observed_min, observed_max=observed_max), code="""
        if (cb_obj.active) {
            observed_min.visible = false;
            observed_max.visible = true;
        } else {
            observed_min.visible = true;
            observed_max.visible = false;
        }
    """)
    # Add callback to toggle visibility
    y2_toggle_callback = CustomJS(args=dict(hist_min=hist_min, hist_max=hist_max), code="""
        if (cb_obj.active) {
            hist_min.visible = false;
            hist_max.visible = true;
        } else {
            hist_min.visible = true;
            hist_max.visible = false;
        }
    """)
    # Add callback to toggle visibility
    y3_toggle_callback = CustomJS(args=dict(ssp245_min=ssp245_min, ssp245_max=ssp245_max), code="""
        if (cb_obj.active) {
            ssp245_min.visible = false;
            ssp245_max.visible = true;
        } else {
            ssp245_min.visible = true;
            ssp245_max.visible = false;
        }
    """)
    # Add callback to toggle visibility
    y4_toggle_callback = CustomJS(args=dict(ssp585_min=ssp585_min, ssp585_max=ssp585_max), code="""
        if (cb_obj.active) {
            ssp585_min.visible = false;
            ssp585_max.visible = true;
        } 
        else {
            ssp585_min.visible = true;
            ssp585_max.visible = false;
        }
    """)
    
    
    # Create toggle buttons
  



   

    # Add callback to toggle visibility
    y1_toggle.js_on_change('active', y1_toggle_callback)
    y2_toggle.js_on_change('active', y2_toggle_callback)
    y3_toggle.js_on_change('active', y3_toggle_callback)
    y4_toggle.js_on_change('active', y4_toggle_callback)
    y5_toggle.js_on_change('active', y5_toggle_callback)
    
    


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
    
    layout = row(y5_toggle,y1_toggle, y2_toggle, y3_toggle, y4_toggle, margin=(30,0, 0, 0))

    # Convert the plot to HTML
    script, div = components((p,layout))


    combined_script = "".join(script)
    combined_div = "".join(div)
    


    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
      
    }
 
    
    return render(request, 'showtemp.html', context)