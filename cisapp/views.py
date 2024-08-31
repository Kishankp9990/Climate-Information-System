from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignupForm, LoginForm

# Create your views here.
#created by developer.

from django.http import HttpResponse
from django.db import connection
from django.http import JsonResponse
import json
from .models import District_average_daily
from bokeh.plotting import figure

from bokeh.embed import components
from bokeh.layouts import column, row
from bokeh.themes import Theme
from bokeh.io import  curdoc
import pandas as pd
from datetime import datetime, timezone
import os
from bokeh.models import HoverTool,TapTool,CustomJS,DataRange1d, Spacer
import xarray as xr
from django.conf import settings
from django.templatetags.static import static
from bokeh.models import Toggle

import requests
import zipfile
import io
import shapefile
import json
from django.http import JsonResponse

from .tasks import process_dataframes_task
from .tasks import process_csv_task
import dill
from django.contrib.sessions.models import Session


def location_wise(request):
    return render(request,'location_wise.html')
def side(request):
    return render(request,'side.html')
def dl_blog(request):
    return render(request,'dl-blog.html')
def climate_snapshot_blog(request):
    return render(request,'climate-snapshot-blog.html')
#.................................................................................................................
# def signup_view(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Signup successful')
#             return redirect('login')
#         else:
#             messages.error(request, 'Signup failed. Please correct the errors below.')
#     else:
#         form = SignupForm()
#     return render(request, 'signup.html', {'form': form})

# def login_view(request):
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 auth_login(request, user)  # Use auth_login to avoid conflict
#                 messages.success(request, 'Login successful')
#                 return redirect('profile')
#             else:
#                 messages.error(request, 'Invalid username or password')
#         else:
#             messages.error(request, 'Login failed. Please correct the errors below.')
#     else:
#         form = LoginForm()
#     return render(request, 'login.html', {'form': form})

# def logout_view(request):
#     auth_logout(request)  # Use auth_logout to avoid conflict
#     messages.success(request, 'Logged out successfully')
#     return redirect('login')

# def profile_view(request):
#     return render(request, 'profile.html')
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Signup successful')
            return redirect('login')
        else:
            messages.error(request, 'Signup failed. Please correct the errors below.')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    auth_login(request, user)  # Use auth_login to avoid conflict
                    messages.success(request, 'Login successful')
                    return redirect('profile')
                else:
                    messages.error(request, 'Invalid email or password')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password')
        else:
            messages.error(request, 'Login failed. Please correct the errors below.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    auth_logout(request)  # Use auth_logout to avoid conflict
    messages.success(request, 'Logged out successfully')
    return redirect('login')

def profile_view(request):
    return render(request, 'profile.html')
#.....................................................................................................................................
def side_by_side(request):
    return render(request,'side-by-side.html')
def shapefile(request):
    return render(request,'shapefile.html')
#.....................................................................................................................................
def district_wise(request):
    return render(request,'district_wise.html')
#.....................................................................................................................................
def river_basin(request):
    return render(request,'river_basin.html')
#.....................................................................................................................................
def index(request):
    return render(request,'index.html')
#.....................................................................................................................................
def basic(request):
    return render(request,'basic.html')
#.....................................................................................................................................
def about(request):
    return render(request,'about.html')
#.....................................................................................................................................
def services(request):
    return render(request,'services.html')
#.....................................................................................................................................
def apps(request):
    return render(request,'apps.html')
#.....................................................................................................................................
def data(request):
    return render(request,'data.html')
#.....................................................................................................................................
def login(request):
    return render(request,'login.html')
#.....................................................................................................................................
def signup(request):
    return render(request,'signup.html')
#.....................................................................................................................................
def map(request):
    return render(request,'map.html')
#.....................................................................................................................................
def netcdf_handler(request):
    return render(request,'netcdf_handler.html')
#.....................................................................................................................................
def dl(request):
    return render(request,'dl.html')
#.....................................................................................................................................

#.................from here real app view starts.......................................................................................
def download_csv(request):
    
    key = request.GET.get('key', None)
    
    if not key:
        return JsonResponse({'error': 'No key provided'}, status=400)
    
    try:
        # Retrieve the session using the key
        session = Session.objects.get(session_key=key)
        session_data = session.get_decoded()
        # Check if the processed data is available in the session
        context_csv = session_data.get('processed_data', None)
        
        return JsonResponse({'data': context_csv})
    
    except Session.DoesNotExist:
        return JsonResponse({'error': 'Session does not exist'}, status=400)
#1.
def mergeppt(df_hist, df_imd, merged_ssp245,merged_ssp585):
    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={'pr': 'hist'})
    df_imd = df_imd.rename(columns={'pr': 'observed'})
    df_ssp245 = merged_ssp245.rename(columns={'pr': 'ssp245'})
    df_ssp585 = merged_ssp585.rename(columns={'pr': 'ssp585'})

    # Merge all DataFrames on their common date-time index
    df_hist_imd = df_hist.join([df_imd], how='outer')
    df_ssp245_ssp585 = df_ssp245.join([ df_ssp585], how='outer')
    
    
    # Merge the DataFrames by concatenating them along the rows (time index)
    merged_df = pd.concat([df_hist_imd, df_ssp245_ssp585])
    
    Data=merged_df.to_csv()
    context_csv = {
        'Data':Data
    }
    
    return context_csv
def mergetmin(df_hist, df_imdaa,merged_ssp245,merged_ssp585):

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={'tasmin': 'hist'})
    df_imdaa = df_imdaa.rename(columns={'tasmin': 'observed'})
    df_ssp245 = merged_ssp245.rename(columns={'tasmin': 'ssp245'})
    df_ssp585 = merged_ssp585.rename(columns={'tasmin': 'ssp585'})

    # Merge all DataFrames on their common date-time index
    df_hist_imdaa = df_hist.join([df_imdaa], how='outer')
    df_ssp245_ssp585 = df_ssp245.join([ df_ssp585], how='outer')
    
    # Merge the DataFrames by concatenating them along the rows (time index)
    merged_df = pd.concat([df_hist_imdaa, df_ssp245_ssp585])
    Data=merged_df.to_csv()
    context_csv = {
        'Data':Data
    }
    
    return context_csv
def mergetmax(df_hist, df_imdaa,merged_ssp245,merged_ssp585):
    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={'tasmax': 'hist'})
    df_imdaa = df_imdaa.rename(columns={'tasmax': 'observed'})
    df_ssp245 = merged_ssp245.rename(columns={'tasmax': 'ssp245'})
    df_ssp585 = merged_ssp585.rename(columns={'tasmax': 'ssp585'})

    # Merge all DataFrames on their common date-time index
    df_hist_imdaa = df_hist.join([df_imdaa], how='outer')
    df_ssp245_ssp585 = df_ssp245.join([ df_ssp585], how='outer')
    
    # Merge the DataFrames by concatenating them along the rows (time index)
    merged_df = pd.concat([df_hist_imdaa, df_ssp245_ssp585])
    Data=merged_df.to_csv()
    context_csv = {
        'Data':Data
    }
    
    return context_csv
def ppt_view_netcdf_annual(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS/Yearly_mean/hist_pr.nc'
    netcdf_file_path_imd ='/home/kishan/datahub/climate/GCM_DS1/temp/pr_interpolated_125_yearly.nc'
    netcdf_file_path_ssp245_near ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_pr_2015_2040.nc'
    netcdf_file_path_ssp585_near ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_pr_2015_2040.nc'
    netcdf_file_path_ssp245_mid ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_pr_2041_2070.nc'
    netcdf_file_path_ssp585_mid ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_pr_2041_2070.nc'
    netcdf_file_path_ssp245_far ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_pr_2071_2100.nc'
    netcdf_file_path_ssp585_far ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_pr_2071_2100.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_imd = xr.open_dataset(netcdf_file_path_imd).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp245_near = xr.open_dataset(netcdf_file_path_ssp245_near).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp585_near= xr.open_dataset(netcdf_file_path_ssp585_near).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp245_mid = xr.open_dataset(netcdf_file_path_ssp245_mid).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp245_far = xr.open_dataset(netcdf_file_path_ssp245_far).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp585_mid = xr.open_dataset(netcdf_file_path_ssp585_mid).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp585_far = xr.open_dataset(netcdf_file_path_ssp585_far).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])

    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    #p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=1600,height=400,sizing_mode='scale_height',toolbar_location=None)
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)

    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')

    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    
    ds_ssp245 = xr.concat([ds_ssp245_near, ds_ssp245_mid, ds_ssp245_far], dim='time')

    # Merge SSP585 datasets
    ds_ssp585 = xr.concat([ds_ssp585_near, ds_ssp585_mid, ds_ssp585_far], dim='time')
    
    # Plot the time series data
    observed=p.line(ds_imd.time, ds_imd.values, legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    # Convert the plot to HTML
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)
    
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(ds_imd)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#2.
def ppt_view_netcdf_monthly(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS1/temp/pr_1979_2014_monthly.nc'
    netcdf_file_path_imd ='/home/kishan/datahub/climate/GCM_DS1/temp/pr_interpolated_125_monthly.nc'
    netcdf_file_path_ssp245 ='/home/kishan/datahub/climate/GCM_DS1/temp/pr_2015_2100_monthly_ssp245.nc'
    netcdf_file_path_ssp585 ='/home/kishan/datahub/climate/GCM_DS1/temp/pr_2015_2100_monthly_ssp585.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_imd = xr.open_dataset(netcdf_file_path_imd).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp245 =xr.open_dataset(netcdf_file_path_ssp245).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp585 =xr.open_dataset(netcdf_file_path_ssp585).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])

    # Convert to DataFrames
    # df_imd = ds_imd.to_dataframe()
    # df_hist = ds_hist.to_dataframe()
    # df_ssp245 = ds_ssp245.to_dataframe()
    # df_ssp585 = ds_ssp585.to_dataframe()
    
    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    #p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=1600,height=400,sizing_mode='scale_height',toolbar_location=None)
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)

    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')

    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(ds_imd.time, ds_imd.values, legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    # Convert the plot to HTML
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)
    
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(ds_imd)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#3.
def ppt_view_netcdf_daily(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS1/EM_imd/historical/pr_1979_2014.nc'
    netcdf_file_path_imd ='/home/kishan/datahub/meteorology/IMD/pr_interpolated_125.nc'
    netcdf_file_path_ssp245 ='/home/kishan/datahub/climate/GCM_DS1/EM/ssp245_pr/pr_2015_2100.nc'
    netcdf_file_path_ssp585 ='/home/kishan/datahub/climate/GCM_DS1/EM/ssp545_pr/pr_2015_2100.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_imd = xr.open_dataset(netcdf_file_path_imd).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp245 =xr.open_dataset(netcdf_file_path_ssp245).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    ds_ssp585 =xr.open_dataset(netcdf_file_path_ssp585).sel(lat=lat, lon=lng, method='nearest').pr.drop_vars(['lat', 'lon'])
    
    # Convert to DataFrames
    # df_imd = ds_imd.to_dataframe()
    # df_hist = ds_hist.to_dataframe()
    # df_ssp245 = ds_ssp245.to_dataframe()
    # df_ssp585 = ds_ssp585.to_dataframe()

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    #p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=1600,height=400,sizing_mode='scale_height',toolbar_location=None)
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)

    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')

    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(ds_imd.time, ds_imd.values, legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)
    
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(ds_imd)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#4.
def ppt_view_csv_daily_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/prec_historical_dist.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/prec_79_23_4x_dist.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/prec_ssp245_dist.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/prec_ssp585_dist.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    
    
    df_imd = df_imd.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    
    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#5.
def ppt_view_csv_monthly_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/prec_historical_dist_monthly.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/prec_79_23_4x_dist_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp245_dist_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp585_dist_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imd = df_imd.loc['1979':'2014']
    

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#6.
def ppt_view_csv_annual_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/prec_historical_dist_yearly.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/prec_79_23_4x_dist_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp245_dist_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp585_dist_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imd = df_imd.loc['1979':'2014']


    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#7.
def ppt_view_csv_daily_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/prec_historical_statewise.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/prec_0.06_79_23_statewise.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/prec_ssp245_state.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/prec_ssp585_state.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    
    
    df_imd = df_imd.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#8.
def ppt_view_csv_monthly_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/prec_historical_statewise_monthly.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/statewise_historival_monthly_yearly/prec_0.06_79_23_statewise_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/prec_ssp245_state_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/prec_ssp585_state_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imd = df_imd.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#9.
def ppt_view_csv_annual_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/prec_historical_statewise_yearly.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/statewise_historival_monthly_yearly/prec_0.06_79_23_statewise_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/prec_ssp245_state_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/prec_ssp585_state_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imd = df_imd.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#10.
def ppt_view_csv_daily_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/prec_historical_basinwise.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/prec_79_23_0.12_river_basin.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/prec_ssp245_basin.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/prec_ssp585_basin.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    
    
    df_imd = df_imd.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#11.
def ppt_view_csv_monthly_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/prec_historical_basinwise_monthly.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/prec_79_23_0.12_river_basin_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp245_basin_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp585_basin_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imd = df_imd.loc['1979':'2014']

    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#12.
def ppt_view_csv_annual_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/prec_historical_basinwise_yearly.csv', usecols=['Date',objectid]) #change it
    df_imd = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/prec_79_23_0.12_river_basin_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp245_basin_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/prec_ssp585_basin_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imd['Date'] = pd.to_datetime(df_imd['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imd.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imd = df_imd.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(df_imd.index, df_imd[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index, df_ssp585[[objectid]], legend_label='ssp585_near',  color='grey', line_width=2,visible=True)
  


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Precipitation", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imd.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#1.
def tmax_view_netcdf_annual(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    
    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS/Yearly_mean/hist_tasmax.nc'
    netcdf_file_path_imdaa ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmax_yearly.nc'
    netcdf_file_path_ssp245_near ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_tasmax_2015_2040.nc'
    netcdf_file_path_ssp585_near ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_tasmax_2015_2040.nc'
    netcdf_file_path_ssp245_mid ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_tasmax_2041_2070.nc'
    netcdf_file_path_ssp585_mid ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_tasmax_2041_2070.nc'
    netcdf_file_path_ssp245_far ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_tasmax_2071_2100.nc'
    netcdf_file_path_ssp585_far ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_tasmax_2071_2100.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon','height'])
    ds_imdaa = xr.open_dataset(netcdf_file_path_imdaa).sel(latitude=lat, longitude=lng, method='nearest').tasmax.drop_vars(['latitude', 'longitude'])
    ds_ssp245_near = xr.open_dataset(netcdf_file_path_ssp245_near).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon','height'])
    ds_ssp585_near= xr.open_dataset(netcdf_file_path_ssp585_near).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon','height'])
    ds_ssp245_mid = xr.open_dataset(netcdf_file_path_ssp245_mid).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon','height'])
    ds_ssp245_far = xr.open_dataset(netcdf_file_path_ssp245_far).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon','height'])
    ds_ssp585_mid = xr.open_dataset(netcdf_file_path_ssp585_mid).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon','height'])
    ds_ssp585_far = xr.open_dataset(netcdf_file_path_ssp585_far).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon','height'])

    v_imdaa=ds_imdaa.sel(time=slice('1979','2014'))
    ds_ssp245 = xr.concat([ds_ssp245_near, ds_ssp245_mid, ds_ssp245_far], dim='time')

    # Merge SSP585 datasets
    ds_ssp585 = xr.concat([ds_ssp585_near, ds_ssp585_mid, ds_ssp585_far], dim='time')
    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(v_imdaa.time, v_imdaa.values, legend_label='imdaa',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585_near',  color='grey', line_width=2,visible=True)

    # Create toggle buttons
    observed_toggle = Toggle(label="observed", active=True, button_type="success")
    hist_toggle = Toggle(label="hist", active=True, button_type="success")
    ssp245_toggle = Toggle(label="ssp245", active=True, button_type="success")
    ssp585_toggle = Toggle(label="ssp585", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))
    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(ds_imdaa)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#2.
def tmax_view_netcdf_monthly(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS1/temp/tasmax_1979_2014_monthly'
    netcdf_file_path_imdaa ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmax_yearly'
    netcdf_file_path_ssp245 ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmax_2015_2100_monthly_ssp245'
    netcdf_file_path_ssp585 ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmax_2015_2100_monthly_ssp585'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon'])
    ds_imdaa = xr.open_dataset(netcdf_file_path_imdaa).sel(latitude=lat, longitude=lng, method='nearest').tasmax.drop_vars(['latitude', 'longitude'])
    ds_ssp245 =xr.open_dataset(netcdf_file_path_ssp245).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon'])
    ds_ssp585 =xr.open_dataset(netcdf_file_path_ssp585).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon'])


    v_imdaa=ds_imdaa.sel(time=slice('1979','2014'))



    

    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(v_imdaa.time, v_imdaa.values, legend_label='imdaa',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585_near',  color='grey', line_width=2,visible=True)

    # Create toggle buttons
    observed_toggle = Toggle(label="observed", active=True, button_type="success")
    hist_toggle = Toggle(label="hist", active=True, button_type="success")
    ssp245_toggle = Toggle(label="ssp245", active=True, button_type="success")
    ssp585_toggle = Toggle(label="ssp585", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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

    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(ds_imdaa)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#3.
def tmax_view_netcdf_daily(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS1/EM/historical/tasmax_1979_2014.nc'
    netcdf_file_path_imdaa ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmax_yearly.nc'
    netcdf_file_path_ssp245 ='/home/kishan/datahub/climate/GCM_DS1/EM/ssp245/tasmax_2015_2100.nc'
    netcdf_file_path_ssp585 ='/home/kishan/datahub/climate/GCM_DS1/EM/ssp585/tasmax_2015_2100.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon'])
    ds_imdaa = xr.open_dataset(netcdf_file_path_imdaa).sel(latitude=lat, longitude=lng, method='nearest').tasmax.drop_vars(['latitude', 'longitude'])
    ds_ssp245 =xr.open_dataset(netcdf_file_path_ssp245).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon'])
    ds_ssp585 =xr.open_dataset(netcdf_file_path_ssp585).sel(lat=lat, lon=lng, method='nearest').tasmax.drop_vars(['lat', 'lon'])

    v_imdaa=ds_imdaa.sel(time=slice('1979','2014'))
    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(v_imdaa.time, v_imdaa.values, legend_label='imdaa',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585_near',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="observed", active=True, button_type="success")
    hist_toggle = Toggle(label="hist", active=True, button_type="success")
    ssp245_toggle = Toggle(label="ssp245", active=True, button_type="success")
    ssp585_toggle = Toggle(label="ssp585", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))
    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(ds_imdaa)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#4.
def tmax_view_csv_daily_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/tasmax_historical_dist.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/tmax_79_23_0.06_dist.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmax_ssp245_dist.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmax_ssp585_dist.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#5.
def tmax_view_csv_monthly_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmax_historical_dist_monthly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmax_79_23_0.06_dist_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp245_dist_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp585_dist_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#6.
def tmax_view_csv_annual_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmax_historical_dist_yearly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmax_79_23_0.06_dist_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp245_dist_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp585_dist_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#7.
def tmax_view_csv_daily_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/tasmax_hist_statewise.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/tmax_79_23_0.06_statewise.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmax_ssp245_state.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmax_ssp585_state.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#8.
def tmax_view_csv_monthly_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmax_hist_statewise_monthly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/statewise_historival_monthly_yearly/tmax_79_23_0.06_statewise_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmax_ssp245_state_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmax_ssp585_state_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#9.
def tmax_view_csv_annual_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmax_hist_statewise_yearly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/statewise_historival_monthly_yearly/tmax_79_23_0.06_statewise_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmax_ssp245_state_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmax_ssp585_state_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#10.
def tmax_view_csv_daily_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/tasmax_historical_basin.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/tmax_79_23_0.12_river_basin.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmax_ssp245_basin.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmax_ssp585_basin.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#11.
def tmax_view_csv_monthly_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmax_historical_basin_monthly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmax_79_23_0.12_river_basin_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp245_basin_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp585_basin_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#12.
def tmax_view_csv_annual_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmax_historical_basin_yearly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmax_79_23_0.12_river_basin_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp245_basin_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmax_ssp585_basin_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmax Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmax", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#1.
def tmin_view_netcdf_annual(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS/Yearly_mean/hist_tasmin.nc'
    netcdf_file_path_imdaa ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmin_yearly.nc'
    netcdf_file_path_ssp245_near ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_tasmin_2015_2040.nc'
    netcdf_file_path_ssp585_near ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_tasmin_2015_2040.nc'
    netcdf_file_path_ssp245_mid ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_tasmin_2041_2070.nc'
    netcdf_file_path_ssp585_mid ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_tasmin_2041_2070.nc'
    netcdf_file_path_ssp245_far ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp245_tasmin_2071_2100.nc'
    netcdf_file_path_ssp585_far ='/home/kishan/datahub/climate/GCM_DS/Yearly_mean/ssp585_tasmin_2071_2100.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon','height'])
    ds__imdaa = xr.open_dataset(netcdf_file_path_imdaa).sel(latitude=lat, longitude=lng, method='nearest').tasmin.drop_vars(['latitude', 'longitude'])
    ds_ssp245_near = xr.open_dataset(netcdf_file_path_ssp245_near).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon','height'])
    ds_ssp585_near= xr.open_dataset(netcdf_file_path_ssp585_near).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon','height'])
    ds_ssp245_mid = xr.open_dataset(netcdf_file_path_ssp245_mid).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon','height'])
    ds_ssp245_far = xr.open_dataset(netcdf_file_path_ssp245_far).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon','height'])
    ds_ssp585_mid = xr.open_dataset(netcdf_file_path_ssp585_mid).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon','height'])
    ds_ssp585_far = xr.open_dataset(netcdf_file_path_ssp585_far).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon','height'])

    v_imdaa=ds__imdaa.sel(time=slice('1979','2014'))
    
    

    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    
    ds_ssp245 = xr.concat([ds_ssp245_near, ds_ssp245_mid, ds_ssp245_far], dim='time')

    # Merge SSP585 datasets
    ds_ssp585 = xr.concat([ds_ssp585_near, ds_ssp585_mid, ds_ssp585_far], dim='time')

    # Plot the time series data
    observed=p.line(v_imdaa.time, v_imdaa.values, legend_label='imdaa',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585_near',  color='grey', line_width=2,visible=True)

    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)
    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(v_imdaa)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#2.
def tmin_view_netcdf_monthly(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS1/temp/tasmin_1979_2014_monthly.nc'
    netcdf_file_path_imdaa ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmin_yearly.nc'
    netcdf_file_path_ssp245 ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmin_2015_2100_monthly_ssp245.nc'
    netcdf_file_path_ssp585 ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmin_2015_2100_monthly_ssp585.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon'])
    ds_imdaa = xr.open_dataset(netcdf_file_path_imdaa).sel(latitude=lat, longitude=lng, method='nearest').tasmin.drop_vars(['latitude', 'longitude'])
    ds_ssp245 =xr.open_dataset(netcdf_file_path_ssp245).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon'])
    ds_ssp585 =xr.open_dataset(netcdf_file_path_ssp585).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon'])
    

    v_imdaa=ds_imdaa.sel(time=slice('1979','2014'))



    

    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(v_imdaa.time, v_imdaa.values, legend_label='imdaa',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585_near',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)
    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(v_imdaa)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#3.
def tmin_view_netcdf_daily(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    


    netcdf_file_path_hist = '/home/kishan/datahub/climate/GCM_DS1/EM/historical/tasmin_1979_2014.nc'
    netcdf_file_path_imdaa ='/home/kishan/datahub/climate/GCM_DS1/temp/tasmin_yearly.nc'
    netcdf_file_path_ssp245 ='/home/kishan/datahub/climate/GCM_DS1/EM/ssp245/tasmin_2015_2100.nc'
    netcdf_file_path_ssp585 ='/home/kishan/datahub/climate/GCM_DS1/EM/ssp585/tasmin_2015_2100.nc'
   

    # Load the datasets
    ds_hist = xr.open_dataset(netcdf_file_path_hist).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon'])
    ds_imdaa = xr.open_dataset(netcdf_file_path_imdaa).sel(latitude=lat, longitude=lng, method='nearest').tasmin.drop_vars(['latitude', 'longitude'])
    ds_ssp245 =xr.open_dataset(netcdf_file_path_ssp245).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon'])
    ds_ssp585 =xr.open_dataset(netcdf_file_path_ssp585).sel(lat=lat, lon=lng, method='nearest').tasmin.drop_vars(['lat', 'lon'])


    v_imdaa=ds_imdaa.sel(time=slice('1979','2014'))

    

    
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(v_imdaa.time, v_imdaa.values, legend_label='imdaa',color='red', line_width=4,visible=True)
    hist_line=p.line(ds_hist.time, ds_hist.values, legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(ds_ssp245.time, ds_ssp245.values, legend_label='ssp245_near',  color='green', line_width=2,visible=True)
    ssp585=p.line(ds_ssp585.time, ds_ssp585.values, legend_label='ssp585_near',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)
    
    df_hist_pickle = dill.dumps(ds_hist)
    df_imd_pickle = dill.dumps(v_imdaa)
    merged_ssp245_pickle = dill.dumps(ds_ssp245)
    merged_ssp585_pickle = dill.dumps(ds_ssp585)
    process_dataframes_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#4.
def tmin_view_csv_daily_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/tasmin_historical_district.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/tmin_79_23_0.06_dist.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmin_ssp245_dist.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmin_ssp585_dist.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active',ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#5.
def tmin_view_csv_monthly_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmin_historical_district_monthly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmin_79_23_0.06_dist_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp245_dist_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp585_dist_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#6.
def tmin_view_csv_annual_district(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmin_historical_district_yearly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmin_79_23_0.06_dist_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp245_dist_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp585_dist_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#7.
def tmin_view_csv_daily_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/tasmin_hist_statewise.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/tmin_79_23_0.06_statewise.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmin_ssp245_state.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmin_ssp585_state.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#8.
def tmin_view_csv_monthly_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmin_hist_statewise_monthly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/statewise_historival_monthly_yearly/tmin_79_23_0.06_statewise_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmin_ssp245_state_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmin_ssp585_state_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    

    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
def tmin_view_csv_annual_state(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmin_hist_statewise_yearly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/statewise_historival_monthly_yearly/tmin_79_23_0.06_statewise_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmin_ssp245_state_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/statewise_future_yearly_monthly/tasmin_ssp585_state_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Annual', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#10.
def tmin_view_csv_daily_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/daily_scale/tasmin_hist_basin.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imd_imdaa_daily/tmin_79_23_0.12_river_basin.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmin_ssp245_basin.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_daily/tasmin_ssp585_basin.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Daily', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#11.
def tmin_view_csv_monthly_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmin_hist_basin_monthly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmin_79_23_0.12_river_basin_monthly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp245_basin_monthly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp585_basin_monthly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']
    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Tmin Monthly', x_axis_type='datetime', width=100,height=100,toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response
#12.
def tmin_view_csv_annual_basin(request):
    objectid = request.GET.get('objectid', None)
    
    df_hist = pd.read_csv('/home/kishan/datahub/Share/kishan/model_emulated_historical/monthly_n_yearly_scale/tasmin_hist_basin_yearly.csv', usecols=['Date',objectid]) #change it
    df_imdaa = pd.read_csv('/home/kishan/datahub/Share/kishan/imdaa_n_imd_data_yearly_monthly_scale/tmin_79_23_0.12_river_basin_yearly.csv', usecols=['Date',objectid])
    df_ssp245= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp245_basin_yearly.csv', usecols=['Date',objectid])
    df_ssp585= pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_yearly_n_monthly_scale/tasmin_ssp585_basin_yearly.csv', usecols=['Date',objectid])
    
    df_hist['Date'] = pd.to_datetime(df_hist['Date'].str.split().str[0], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_hist.set_index('Date', inplace=True)
    df_imdaa['Date'] = pd.to_datetime(df_imdaa['Date'], format='%Y-%m-%d')  #when date format is "%Y-%m-%d"
    df_imdaa.set_index('Date', inplace=True)
    df_ssp245['Date'] = pd.to_datetime(df_ssp245['Date'].str.split().str[0], format='%Y-%m-%d') #when date format is "%Y-%m-%d": " 12:00:00"
    df_ssp245.set_index('Date', inplace=True)
    df_ssp585['Date'] = pd.to_datetime(df_ssp585['Date'].str.split().str[0], format='%Y-%m-%d')
    df_ssp585.set_index('Date', inplace=True)
    df_imdaa = df_imdaa.loc['1979':'2014']

    # Create a Bokeh figure
    # p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(0,0, 0, -265))
    p = figure(x_axis_label='Date', y_axis_label='Precipitation Annual', x_axis_type='datetime', width=100,height=100, toolbar_location=None)
    
    
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)


    # Plot the time series data
    observed=p.line(df_imdaa.index, df_imdaa[[objectid]], legend_label='imd',color='red', line_width=4,visible=True)
    hist_line=p.line(df_hist.index, df_hist[[objectid]], legend_label='hist', color='orange', line_width=2,visible=True)
    ssp245=p.line(df_ssp245.index, df_ssp245[[objectid]], legend_label='ssp245',  color='green', line_width=2,visible=True)
    ssp585=p.line(df_ssp585.index,df_ssp585[[objectid]], legend_label='ssp585',  color='grey', line_width=2,visible=True)


    # Create toggle buttons
    observed_toggle = Toggle(label="Observed", active=True, button_type="success")
    hist_toggle = Toggle(label="Historical", active=True, button_type="success")
    ssp245_toggle = Toggle(label="SSP 2.45 ", active=True, button_type="success")
    ssp585_toggle = Toggle(label="SSP 5.85 ", active=True, button_type="success")

    # Add callback to toggle visibility
    hist_toggle.js_link('active', hist_line, 'visible')
    observed_toggle.js_link('active', observed, 'visible')
    ssp245_toggle.js_link('active', ssp245, 'visible')
    ssp585_toggle.js_link('active', ssp585, 'visible')

    
    # CustomJS callback to change the button color based on active state
    callback_code = """
        if (cb_obj.active) {
            cb_obj.button_type = "success"; //green
        } else {
            cb_obj.button_type = "default"; 
        }
    """

    hist_toggle.js_on_change('active', CustomJS(code=callback_code))
    observed_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp245_toggle.js_on_change('active', CustomJS(code=callback_code))
    ssp585_toggle.js_on_change('active', CustomJS(code=callback_code))


    

    # Hide the Bokeh logo from the toolbar
    p.toolbar.logo = None
    p.legend.visible=False

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Date", "@x{%d/%m/%Y}"),
        ("Tmin", "@y"),
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
    
    # Add a spacer to give space between the plot and the toggle buttons
    spacer = Spacer(width=0)

    
    
    toggle = column(hist_toggle,observed_toggle,ssp245_toggle,ssp585_toggle, spacing=10, margin=(35, 0, 0, 0))
    layout=row(p,spacer,toggle)
    # Attach the layout to the current document
    curdoc().add_root(layout)
    # Convert the plot to HTML
    script, div = components(layout)

    combined_script = "".join(script)
    combined_div = "".join(div)

    df_hist.index = pd.to_datetime(df_hist.index)  # Assuming your index is already in datetime format, otherwise, convert it

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={objectid: 'hist'})
    df_imd = df_imdaa.rename(columns={objectid: 'observed'})
    df_ssp245 = df_ssp245.rename(columns={objectid: 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={objectid: 'ssp585'})
    request.session.save()

    # Trigger the Celery task to process the time-consuming task
    session_key =request.session.session_key
    # Merge and store the result in the session
    context = {
        'script': combined_script,
        'div': combined_div,
        'key': session_key
    }
    response = render(request, 'dashboard.html', context)

    
    df_hist_pickle = dill.dumps(df_hist)
    df_imd_pickle = dill.dumps(df_imd)
    merged_ssp245_pickle = dill.dumps(df_ssp245)
    merged_ssp585_pickle = dill.dumps(df_ssp585)
    process_csv_task.delay(df_hist_pickle, df_imd_pickle, merged_ssp245_pickle, merged_ssp585_pickle, session_key)

    return response

#..................................................................................................................
def plotting(request):
    # Execute raw SQL query to fetch all rows from columns A and B
    with connection.cursor() as cursor:
        query = "SELECT Dates, Nainital FROM District_average_daily1;"
        cursor.execute(query)
        rows = cursor.fetchall()

    # Pass the fetched rows to the template
    return render(request, 'plotting.html', {'rows': rows})
#....................................................................................................................................

def sf_db_styling(request):
    date_to_fetch = request.GET.get('date_to_fetch', '1990-04-25') 
    

    # Execute raw SQL query to fetch rows corresponding to the given date
    with connection.cursor() as cursor:
        query = "SELECT * FROM District_average_daily WHERE date = %s;"
        cursor.execute(query, [date_to_fetch])
        rows = cursor.fetchall()
        #print(*rows)  #this syntax is used to print list in a console with space.
        print("hii")
    # Extract column names
    columns = [desc[0] for desc in cursor.description]
# Pass the fetched rows and column names to the template
    return render(request, 'sf_db_styling.html', {'rows': rows, 'columns': columns})  
#....................................................................................................................................

def sf_db(request):
    return render(request, 'sf_db.html')

#supporting view
def aSync(request):                                     
    date_to_query = request.GET.get('date_to_query', '1979-04-25')  
    # column_name = request.GET.get('column_name', 'Samastipur')  # The column name you want to fetch, you can change this as needed
    column_name = request.GET.get('object_id', '1')

    # Execute raw SQL query to fetch specific row from column B
    with connection.cursor() as cursor:
        query = "SELECT `{}` FROM District_average_daily WHERE date = %s;".format(column_name)
        cursor.execute(query, [date_to_query])
        column_b_value = cursor.fetchone()[0]  # Assuming there's only one value for the given date

    # Return the fetched data as JSON response
    return JsonResponse({'Object-id':column_name,'PrecipitationValue': column_b_value})

def sf(request):
    return render(request,'sf.html')


#.....................................................................................................................................

def bokeh(request):
 
   #create a plot
   plot = figure(outer_width=400, outer_height=400)
 
   # add a circle renderer with a size, color, and alpha
 
   plot.circle([1, 2, 3, 4, 5], [6, 7, 2, 4, 5], size=20, color="navy", alpha=0.5)
 
   script, div = components(plot)
 
   return render(request, 'bokeh.html', {'script': script, 'div': div})


def timeSeriesData(request):
    # Sample time series data (replace with your own data)
    data = {
        'date': [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
        'value': [5, 15, 10]
    }

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Value', x_axis_type='datetime')

    # Plot the time series data
    p.line(df['date'], df['value'], legend_label='Value', line_width=2)

    # Convert the plot to HTML
    script, div = components(p)

    # Pass the script and div to the template
    context = {
        'script': script,
        'div': div,
    }
    
    return render(request, 'timeSeriesData.html', context)
#.........................................................................................................................................

def sfppt(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    objectid = request.GET.get('objectid', None)
    
    print(objectid)
    
    # Define path to NetCDF file (assuming 'nc' subfolder in static)


# Read the CSV file and parse dates
    df = pd.read_csv('/home/kishan/my_data/prec_merged_79_2023.csv')
    df2 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/prec_ssp245_dist.csv')
    df3 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/prec_ssp585_dist.csv')
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df.set_index('date', inplace=True)
    df2['Date'] = pd.to_datetime(df2['Date'].str.split().str[0], format='%Y-%m-%d')
    df2.set_index('Date', inplace=True)
    df3['Date'] = pd.to_datetime(df3['Date'].str.split().str[0], format='%Y-%m-%d')
    df3.set_index('Date', inplace=True)
    # Ensure the column name exists
    if objectid not in df.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df2.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df3.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    

    # Filter data for the selected objectid
    df_filtered = df[[objectid]]
    df_filtered_yearly=df_filtered.resample('Y').sum()
    df_filtered2 = df2[[objectid]]
    df_filtered_yearly2=df_filtered2.resample('Y').sum()
    df_filtered3 = df3[[objectid]]
    df_filtered_yearly3=df_filtered3.resample('Y').sum()

    
    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(-20,0, 0, -265))
    
    


    # theme = Theme(json={
    #     'attrs': {
    #         'Figure': {
    #             'background_fill_color': '#2F2F2F',
    #             'border_fill_color': '#2F2F2F',
    #             'outline_line_color': '#444444'
    #             },
    #         'Axis': {
    #             'axis_line_color': "white",
    #             'axis_label_text_color': "white",
    #             'major_label_text_color': "white",
    #             'major_tick_line_color': "white",
    #             'minor_tick_line_color': "white",
    #             'minor_tick_line_color': "white"
    #             },
    #         'Grid': {
    #             'grid_line_dash': [6, 4],
    #             'grid_line_alpha': .3
    #             },
    #         'Circle': {
    #             'fill_color': 'lightblue',
    #             'size': 10,
    #             },
    #         'Title': {
    #             'text_color': "white"
    #             }
    #         }
    #     })
    # Load and apply the custom theme
    theme_path = os.path.join(os.path.dirname(__file__), 'static/yml/transparent_theme.yml')
    print(theme_path)
    theme = Theme(filename=theme_path)
    curdoc().theme=theme
    curdoc().add_root(p)
    
    
    

    # Plot the time series data
    # p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='imd', line_width=2)
    hist_line=p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='hist', color='orange', line_width=2)
    ssp245_line=p.line(df_filtered_yearly2.index, df_filtered_yearly2[objectid], legend_label='ssp245',  color='red', line_width=2)
    ssp585_line=p.line(df_filtered_yearly3.index, df_filtered_yearly3[objectid], legend_label='ssp585',  color='green', line_width=2)


    # Create toggle buttons
    y1_toggle = Toggle(label="hist", active=True, button_type="success")
    y2_toggle = Toggle(label="ssp245", active=True, button_type="success")
    y3_toggle = Toggle(label="ssp585", active=True, button_type="success")

    # Add callback to toggle visibility
    y1_toggle.js_link('active', hist_line, 'visible')
    y2_toggle.js_link('active', ssp245_line, 'visible')
    y3_toggle.js_link('active', ssp585_line, 'visible')

    

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
    
    layout = row(y1_toggle, y2_toggle, y3_toggle,margin=(30,0, 0, 0))


    # Convert the plot to HTML
    script, div = components((p,layout))


    combined_script = "".join(script)
    combined_div = "".join(div)

    # df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # # Drop latitude and longitude columns
    # df = df.drop(columns=['latitude', 'longitude'])

    # Convert data to CSV format
    csv_data_ppt = df_filtered.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        'csv_data': csv_data_ppt,
    }


    return render(request, 'sfppt.html', context)

def sfws(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    objectid = request.GET.get('objectid', None)
    
    
    print(objectid)
    
# Read the CSV file and parse dates
    df = pd.read_csv('/home/kishan/my_data/District_average_daily.csv')
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df.set_index('date', inplace=True)

    # Ensure the column name exists
    if objectid not in df.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    

    # Filter data for the selected objectid
    df_filtered = df[[objectid]]
    df_filtered_yearly=df_filtered.resample('Y').sum()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Wind Speed', x_axis_type='datetime', width=1000)
    print(df.index)

    # Plot the wind speed
    p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='Wind Speed', line_width=2, color='blue')

    # y2 = 3
    y2 = [3] * len(df)
    orange_line = p.line(df.index, y2, legend_label='Y2', line_width=2, color='orange', visible=False)

    # y1 = 1
    y1 = [1] * len(df)
    green_line = p.line(df.index, y1, legend_label='Y1', line_width=2, color='green', visible=False)

    # y3 = 5
    y3 = [5] * len(df)
    red_line = p.line(df.index, y3, legend_label='Y3', line_width=2, color='red', visible=False)

    # Create toggle buttons
    y2_toggle = Toggle(label="Y2", active=True, button_type="success")
    y1_toggle = Toggle(label="Y1", active=True, button_type="success")
    y3_toggle = Toggle(label="Y3", active=True, button_type="success")

    # Set visibility of lines to True
    orange_line.visible = True
    green_line.visible = True
    red_line.visible = True    

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

    # df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # # Drop latitude and longitude columns
    # df = df.drop(columns=['lat', 'lon'])

    # Convert data to CSV format
    csv_data_ws = df_filtered.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        'csv_data': csv_data_ws
        
    }

    return render(request, 'sfws.html', context)

def sftemp(request):
    
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    objectid = request.GET.get('objectid', None)
    
    print(objectid)
    
    # Define path to NetCDF file (assuming 'nc' subfolder in static)

    df = pd.read_csv('/home/kishan/my_data/tmax_merged_79_2022.csv')
    df1 = pd.read_csv('/home/kishan/my_data/tmin_merged_79_2022.csv')
    df2 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmax_ssp245_dist.csv')
    df3 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmax_ssp585_dist.csv')
    df4 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmin_ssp245_dist.csv')
    df5 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmin_ssp585_dist.csv')
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df.set_index('date', inplace=True)
    df1['date'] = pd.to_datetime(df1['date'], format='%Y-%m-%d')
    df1.set_index('date', inplace=True)
    df2['Date'] = pd.to_datetime(df2['Date'].str.split().str[0], format='%Y-%m-%d')
    df2.set_index('Date', inplace=True)
    df3['Date'] = pd.to_datetime(df3['Date'].str.split().str[0], format='%Y-%m-%d')
    df3.set_index('Date', inplace=True)
    df4['Date'] = pd.to_datetime(df4['Date'].str.split().str[0], format='%Y-%m-%d')
    df4.set_index('Date', inplace=True)
    df5['Date'] = pd.to_datetime(df5['Date'].str.split().str[0], format='%Y-%m-%d')
    df5.set_index('Date', inplace=True)
    # Ensure the column name exists
    if objectid not in df.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df1.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df2.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df3.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df4.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df5.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    # Filter data for the selected objectid
    df_filtered = df[[objectid]]
    df_filtered_yearly=df_filtered.resample('Y').mean()
    # Filter data for the selected objectid
    df1_filtered = df1[[objectid]]
    df1_filtered_yearly=df1_filtered.resample('Y').mean()
    df2_filtered = df2[[objectid]]
    df2_filtered_yearly=df2_filtered.resample('Y').mean()
    df3_filtered = df3[[objectid]]
    df3_filtered_yearly=df3_filtered.resample('Y').mean()
    df4_filtered = df4[[objectid]]
    df4_filtered_yearly=df4_filtered.resample('Y').mean()
    df5_filtered = df5[[objectid]]
    df5_filtered_yearly=df5_filtered.resample('Y').mean()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Temp', x_axis_type='datetime', width=700, margin=(-20,0, 0, -265))

    

    # Plot the time series data
    tmax_hist=p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='tmax_hist', line_width=2, color="green")
    tmin_hist=p.line(df1_filtered_yearly.index, df1_filtered_yearly[objectid], legend_label='tmin_hist', line_width=0.5, color="green",visible=False)
    tmax_ssp245=p.line(df2_filtered_yearly.index, df2_filtered_yearly[objectid], legend_label='tmax_ssp245', line_width=0.5, color="red")
    tmax_ssp585=p.line(df3_filtered_yearly.index, df3_filtered_yearly[objectid], legend_label='tmax_ssp585', line_width=0.5, color="blue")
    tmin_ssp245=p.line(df4_filtered_yearly.index, df4_filtered_yearly[objectid], legend_label='tmin_ssp245', line_width=0.5, color="red",visible=False)
    tmin_ssp585=p.line(df5_filtered_yearly.index, df5_filtered_yearly[objectid], legend_label='tmin_ssp585', line_width=0.5, color="blue",visible=False)


    # Create toggle buttons
    y5_toggle = Toggle(label="Show Min", active=False, button_type="success")
    y2_toggle = Toggle(label="hist", active=False, button_type="success")
    y3_toggle = Toggle(label="ssp245", active=False, button_type="success")
    y4_toggle = Toggle(label="ssp585", active=False, button_type="success")

    # Add callback to toggle visibility for max/min
    y5_toggle_callback = CustomJS(args=dict(toggle5=y5_toggle,toggle4=y4_toggle,toggle3=y3_toggle,toggle2=y2_toggle,
        tmin_hist=tmin_hist, tmax_hist=tmax_hist,
        tmin_ssp245=tmin_ssp245, tmax_ssp245=tmax_ssp245,
        tmin_ssp585=tmin_ssp585, tmax_ssp585=tmax_ssp585
    ), code="""
        if (cb_obj.active) {
            toggle2.active=false;
            toggle3.active=false;
            toggle4.active=false;
            toggle5.label="show max";
            tmin_hist.visible = true;
            tmax_hist.visible = false;
            tmin_ssp245.visible = true;
            tmax_ssp245.visible = false;
            tmin_ssp585.visible = true;
            tmax_ssp585.visible = false;
        }else{
            toggle2.active=true;
            toggle3.active=true;
            toggle4.active=true;
            toggle5.label="show min";
            tmin_hist.visible = false;
            tmax_hist.visible = true;
            tmin_ssp245.visible = false;
            tmax_ssp245.visible = true;
            tmin_ssp585.visible = false;
            tmax_ssp585.visible = true;
            
        }
    """)
    # Add callback to toggle visibility
    y2_toggle_callback = CustomJS(args=dict(tmin_hist=tmin_hist, tmax_hist=tmax_hist), code="""
        if (cb_obj.active) {
            tmin_hist.visible = false;
            tmax_hist.visible = true;
        } else {
            tmin_hist.visible = true;
            tmax_hist.visible = false;
        }
    """)
    # Add callback to toggle visibility
    y3_toggle_callback = CustomJS(args=dict(tmin_ssp245=tmin_ssp245, tmax_ssp245=tmax_ssp245), code="""
        if (cb_obj.active) {
            tmin_ssp245.visible = false;
            tmax_ssp245.visible = true;
        } else {
            tmin_ssp245.visible = true;
            tmax_ssp245.visible = false;
        }
    """)
    # Add callback to toggle visibility
    y4_toggle_callback = CustomJS(args=dict(tmin_ssp585=tmin_ssp585, tmax_ssp585=tmax_ssp585), code="""
        if (cb_obj.active) {
            tmin_ssp585.visible = false;
            tmax_ssp585.visible = true;
        } 
        else {
            tmin_ssp585.visible = true;
            tmax_ssp585.visible = false;
        }
    """)

    # Add callback to toggle visibility
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

    layout = row(y5_toggle, y2_toggle, y3_toggle, y4_toggle, margin=(30,0, 0, 0))

    # Convert the plot to HTML
    script, div = components((p,layout))


    combined_script = "".join(script)
    combined_div = "".join(div)
    
    # df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # # Drop latitude and longitude columns
    # df = df.drop(columns=['latitude', 'longitude'])

    # Convert data to CSV format
    merged_df = pd.merge(df_filtered, df1_filtered, on='date', suffixes=('_tmax', '_tmin'))
    csv_data_temp = merged_df.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        'csv_data': csv_data_temp,
    }
    print(csv_data_temp)
    
    return render(request, 'sftemp.html', context)

#....................................................................................................................................................

def pptbasin(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    objectid = request.GET.get('objectid', None)
    
    print(objectid)
    
    # Define path to NetCDF file (assuming 'nc' subfolder in static)


# Read the CSV file and parse dates
    df = pd.read_csv('/home/kishan/datahub/Share/kishan/Data/pr_dist_0.12_79_2023_river_basin.csv')
    df2 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/prec_ssp245_basin.csv')
    df3 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/prec_ssp585_basin.csv')
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df.set_index('date', inplace=True)
    df2['Date'] = pd.to_datetime(df2['Date'].str.split().str[0], format='%Y-%m-%d')
    df2.set_index('Date', inplace=True)
    df3['Date'] = pd.to_datetime(df3['Date'].str.split().str[0], format='%Y-%m-%d')
    df3.set_index('Date', inplace=True)
    # Ensure the column name exists
    if objectid not in df.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df2.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df3.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    

    # Filter data for the selected objectid
    df_filtered = df[[objectid]]
    df_filtered_yearly=df_filtered.resample('Y').sum()
    df_filtered2 = df2[[objectid]]
    df_filtered_yearly2=df_filtered2.resample('Y').sum()
    df_filtered3 = df3[[objectid]]
    df_filtered_yearly3=df_filtered3.resample('Y').sum()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='PPT', x_axis_type='datetime', width=700, margin=(-20,0, 0, -265))
    
    

    # Plot the time series data
    # p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='imd', line_width=2)
    hist_line=p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='hist', color='orange', line_width=2)
    ssp245_line=p.line(df_filtered_yearly2.index, df_filtered_yearly2[objectid], legend_label='ssp245',  color='red', line_width=2)
    ssp585_line=p.line(df_filtered_yearly3.index, df_filtered_yearly3[objectid], legend_label='ssp585',  color='green', line_width=2)


    # Create toggle buttons
    y1_toggle = Toggle(label="hist", active=True, button_type="success")
    y2_toggle = Toggle(label="ssp245", active=True, button_type="success")
    y3_toggle = Toggle(label="ssp585", active=True, button_type="success")

    # Add callback to toggle visibility
    y1_toggle.js_link('active', hist_line, 'visible')
    y2_toggle.js_link('active', ssp245_line, 'visible')
    y3_toggle.js_link('active', ssp585_line, 'visible')

    

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
    
    layout = row(y1_toggle, y2_toggle, y3_toggle,margin=(30,0, 0, 0))

    # Convert the plot to HTML
    script, div = components((p,layout))


    combined_script = "".join(script)
    combined_div = "".join(div)

    # df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # # Drop latitude and longitude columns
    # df = df.drop(columns=['latitude', 'longitude'])

    # Convert data to CSV format
    csv_data_ppt = df_filtered.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        'csv_data': csv_data_ppt,
    }


    return render(request, 'sfppt.html', context)

def wsbasin(request):
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    objectid = request.GET.get('objectid', None)
    
    
    print(objectid)
    
# Read the CSV file and parse dates
    df = pd.read_csv('/home/kishan/my_data/District_average_daily.csv')
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df.set_index('date', inplace=True)

    # Ensure the column name exists
    if objectid not in df.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    

    # Filter data for the selected objectid
    df_filtered = df[[objectid]]
    df_filtered_yearly=df_filtered.resample('Y').sum()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Wind Speed', x_axis_type='datetime', width=1000)
    print(df.index)

    # Plot the wind speed
    p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='Wind Speed', line_width=2, color='blue')

    # y2 = 3
    y2 = [3] * len(df)
    orange_line = p.line(df.index, y2, legend_label='Y2', line_width=2, color='orange', visible=False)

    # y1 = 1
    y1 = [1] * len(df)
    green_line = p.line(df.index, y1, legend_label='Y1', line_width=2, color='green', visible=False)

    # y3 = 5
    y3 = [5] * len(df)
    red_line = p.line(df.index, y3, legend_label='Y3', line_width=2, color='red', visible=False)

    # Create toggle buttons
    y2_toggle = Toggle(label="Y2", active=True, button_type="success")
    y1_toggle = Toggle(label="Y1", active=True, button_type="success")
    y3_toggle = Toggle(label="Y3", active=True, button_type="success")

    # Set visibility of lines to True
    orange_line.visible = True
    green_line.visible = True
    red_line.visible = True    

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

    # df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # # Drop latitude and longitude columns
    # df = df.drop(columns=['lat', 'lon'])

    # Convert data to CSV format
    csv_data_ws = df_filtered.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        'csv_data': csv_data_ws
        
    }

    return render(request, 'sfws.html', context)

def tempbasin(request):
    
    lat = request.GET.get('lat', None)
    lng = request.GET.get('lng', None)
    objectid = request.GET.get('objectid', None)
    
    print(objectid)
    
    # Define path to NetCDF file (assuming 'nc' subfolder in static)

    df = pd.read_csv('/home/kishan/datahub/Share/kishan/Data/tmax_dist_0.12_79_20_river_basin')
    df1 = pd.read_csv('/home/kishan/datahub/Share/kishan/Data/tmin_dist_0.12_79_20_river_basin')
    df2 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmax_ssp245_basin.csv')
    df3 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmax_ssp585_basin.csv')
    df4 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmin_ssp245_basin.csv')
    df5 = pd.read_csv('/home/kishan/datahub/Share/kishan/future_data_final/tasmin_ssp585_basin.csv')
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df.set_index('date', inplace=True)
    df1['date'] = pd.to_datetime(df1['date'], format='%Y-%m-%d')
    df1.set_index('date', inplace=True)
    df2['Date'] = pd.to_datetime(df2['Date'].str.split().str[0], format='%Y-%m-%d')
    df2.set_index('Date', inplace=True)
    df3['Date'] = pd.to_datetime(df3['Date'].str.split().str[0], format='%Y-%m-%d')
    df3.set_index('Date', inplace=True)
    df4['Date'] = pd.to_datetime(df4['Date'].str.split().str[0], format='%Y-%m-%d')
    df4.set_index('Date', inplace=True)
    df5['Date'] = pd.to_datetime(df5['Date'].str.split().str[0], format='%Y-%m-%d')
    df5.set_index('Date', inplace=True)
    # Ensure the column name exists
    if objectid not in df.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df1.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df2.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df3.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df4.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    if objectid not in df5.columns:
        return JsonResponse({'error': 'Invalid objectid'}, status=400)
    # Filter data for the selected objectid
    df_filtered = df[[objectid]]
    df_filtered_yearly=df_filtered.resample('Y').mean()
    # Filter data for the selected objectid
    df1_filtered = df1[[objectid]]
    df1_filtered_yearly=df1_filtered.resample('Y').mean()
    df2_filtered = df2[[objectid]]
    df2_filtered_yearly=df2_filtered.resample('Y').mean()
    df3_filtered = df3[[objectid]]
    df3_filtered_yearly=df3_filtered.resample('Y').mean()
    df4_filtered = df4[[objectid]]
    df4_filtered_yearly=df4_filtered.resample('Y').mean()
    df5_filtered = df5[[objectid]]
    df5_filtered_yearly=df5_filtered.resample('Y').mean()

    # Create a Bokeh figure
    p = figure(title="Time Series Plot", x_axis_label='Date', y_axis_label='Temp', x_axis_type='datetime', width=700, margin=(-20,0, 0, -265))

    

    # Plot the time series data
    tmax_hist=p.line(df_filtered_yearly.index, df_filtered_yearly[objectid], legend_label='tmax_hist', line_width=2, color="green")
    tmin_hist=p.line(df1_filtered_yearly.index, df1_filtered_yearly[objectid], legend_label='tmin_hist', line_width=0.5, color="green",visible=False)
    tmax_ssp245=p.line(df2_filtered_yearly.index, df2_filtered_yearly[objectid], legend_label='tmax_ssp245', line_width=0.5, color="red")
    tmax_ssp585=p.line(df3_filtered_yearly.index, df3_filtered_yearly[objectid], legend_label='tmax_ssp585', line_width=0.5, color="blue")
    tmin_ssp245=p.line(df4_filtered_yearly.index, df4_filtered_yearly[objectid], legend_label='tmin_ssp245', line_width=0.5, color="red",visible=False)
    tmin_ssp585=p.line(df5_filtered_yearly.index, df5_filtered_yearly[objectid], legend_label='tmin_ssp585', line_width=0.5, color="blue",visible=False)


    # Create toggle buttons
    y5_toggle = Toggle(label="Show Min", active=False, button_type="success")
    y2_toggle = Toggle(label="hist", active=False, button_type="success")
    y3_toggle = Toggle(label="ssp245", active=False, button_type="success")
    y4_toggle = Toggle(label="ssp585", active=False, button_type="success")

    # Add callback to toggle visibility for max/min
    y5_toggle_callback = CustomJS(args=dict(toggle5=y5_toggle,toggle4=y4_toggle,toggle3=y3_toggle,toggle2=y2_toggle,
        tmin_hist=tmin_hist, tmax_hist=tmax_hist,
        tmin_ssp245=tmin_ssp245, tmax_ssp245=tmax_ssp245,
        tmin_ssp585=tmin_ssp585, tmax_ssp585=tmax_ssp585
    ), code="""
        if (cb_obj.active) {
            toggle2.active=false;
            toggle3.active=false;
            toggle4.active=false;
            toggle5.label="show max";
            tmin_hist.visible = true;
            tmax_hist.visible = false;
            tmin_ssp245.visible = true;
            tmax_ssp245.visible = false;
            tmin_ssp585.visible = true;
            tmax_ssp585.visible = false;
        }else{
            toggle2.active=true;
            toggle3.active=true;
            toggle4.active=true;
            toggle5.label="show min";
            tmin_hist.visible = false;
            tmax_hist.visible = true;
            tmin_ssp245.visible = false;
            tmax_ssp245.visible = true;
            tmin_ssp585.visible = false;
            tmax_ssp585.visible = true;
            
        }
    """)
    # Add callback to toggle visibility
    y2_toggle_callback = CustomJS(args=dict(tmin_hist=tmin_hist, tmax_hist=tmax_hist), code="""
        if (cb_obj.active) {
            tmin_hist.visible = false;
            tmax_hist.visible = true;
        } else {
            tmin_hist.visible = true;
            tmax_hist.visible = false;
        }
    """)
    # Add callback to toggle visibility
    y3_toggle_callback = CustomJS(args=dict(tmin_ssp245=tmin_ssp245, tmax_ssp245=tmax_ssp245), code="""
        if (cb_obj.active) {
            tmin_ssp245.visible = false;
            tmax_ssp245.visible = true;
        } else {
            tmin_ssp245.visible = true;
            tmax_ssp245.visible = false;
        }
    """)
    # Add callback to toggle visibility
    y4_toggle_callback = CustomJS(args=dict(tmin_ssp585=tmin_ssp585, tmax_ssp585=tmax_ssp585), code="""
        if (cb_obj.active) {
            tmin_ssp585.visible = false;
            tmax_ssp585.visible = true;
        } 
        else {
            tmin_ssp585.visible = true;
            tmax_ssp585.visible = false;
        }
    """)

    # Add callback to toggle visibility
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

    layout = row(y5_toggle, y2_toggle, y3_toggle, y4_toggle, margin=(30,0, 0, 0))

    # Convert the plot to HTML
    script, div = components((p,layout))


    combined_script = "".join(script)
    combined_div = "".join(div)
    
    # df.index = pd.to_datetime(df.index)  # Assuming your index is already in datetime format, otherwise, convert it
    # # Drop latitude and longitude columns
    # df = df.drop(columns=['latitude', 'longitude'])

    # Convert data to CSV format
    merged_df = pd.merge(df_filtered, df1_filtered, on='date', suffixes=('_tmax', '_tmin'))
    csv_data_temp = merged_df.to_csv()

    # Pass the CSV data along with the script and div to the template
    context = {
        'script': combined_script,
        'div': combined_div,
        'csv_data': csv_data_temp,
    }
    print(csv_data_temp)
    
    return render(request, 'sftemp.html', context)

# timeline
# 2015-2040: near future 
# 2041-2070: mid future 
# 2071-2100: far future



def dbTesting(request):
    date_to_query = '1986-04-25' 
    column_name = 'Nainital'  # The column name you want to fetch, you can change this as needed

    # Execute raw SQL query to fetch specific row from column B
    with connection.cursor() as cursor:
        query = "SELECT `{}` FROM District_average_daily1 WHERE Dates = %s;".format(column_name)
        cursor.execute(query, [date_to_query])
        column_b_value = cursor.fetchone()[0]  # Assuming there's only one value for the given date

    # Pass the fetched value and column name to the template
    return render(request, 'dbTesting.html', {'column_b_value': column_b_value, 'column_name': column_name})
#.....................................................................................................................................