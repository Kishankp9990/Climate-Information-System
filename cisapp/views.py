from django.shortcuts import render

# Create your views here.
#created by developer.
from django.http import HttpResponse
from django.db import connection
from django.http import JsonResponse
import json
from .models import District_average_daily
from bokeh.plotting import figure
from bokeh.embed import components
import pandas as pd
from datetime import datetime, timezone
import os

def dbTesting(request):
    date_to_query = '25-04-1986'  
    column_name = 'Nainital'  # The column name you want to fetch, you can change this as needed

    # Execute raw SQL query to fetch specific row from column B
    with connection.cursor() as cursor:
        query = "SELECT `{}` FROM District_average_daily1 WHERE Dates = %s;".format(column_name)
        cursor.execute(query, [date_to_query])
        column_b_value = cursor.fetchone()[0]  # Assuming there's only one value for the given date

    # Pass the fetched value and column name to the template
    return render(request, 'dbTesting.html', {'column_b_value': column_b_value, 'column_name': column_name})
#.....................................................................................................................................
def location(request):
    return render(request,'location.html')
#.....................................................................................................................................
def index(request):
    return render(request,'index.html')
#.....................................................................................................................................
def basic(request):
    return render(request,'basic.html')
#.....................................................................................................................................

def map(request):
    return render(request,'map.html')
#.....................................................................................................................................

def netcdf_handler(request):
    return render(request,'netcdf_handler.html')
#.....................................................................................................................................

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
    date_to_fetch = request.GET.get('date_to_fetch', '25-04-1990') 
    

    # Execute raw SQL query to fetch rows corresponding to the given date
    with connection.cursor() as cursor:
        query = "SELECT * FROM District_average_daily WHERE MyUnknownColumn = %s;"
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
    date_to_query = request.GET.get('date_to_query', '25-04-1986')  
    column_name = request.GET.get('column_name', 'Samastipur')  # The column name you want to fetch, you can change this as needed

    # Execute raw SQL query to fetch specific row from column B
    with connection.cursor() as cursor:
        query = "SELECT `{}` FROM District_average_daily1 WHERE Dates = %s;".format(column_name)
        cursor.execute(query, [date_to_query])
        column_b_value = cursor.fetchone()[0]  # Assuming there's only one value for the given date

    # Return the fetched data as JSON response
    return JsonResponse({'DistrictName':column_name,'PrecipitationValue': column_b_value})

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














