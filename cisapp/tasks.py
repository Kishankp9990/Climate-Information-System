# myapp/tasks.py

from celery import shared_task
import pandas as pd
import io
import dill
import xarray as xr

from django.core.exceptions import ObjectDoesNotExist

@shared_task
def process_dataframes_task(va_hist_pickle, va_imd_pickle, va_merged_ssp245_pickle, va_merged_ssp585_pickle, session_key):
    va_hist = dill.loads(va_hist_pickle)
    va_imd = dill.loads(va_imd_pickle)
    va_merged_ssp245 = dill.loads(va_merged_ssp245_pickle)
    va_merged_ssp585 = dill.loads(va_merged_ssp585_pickle)

    # Create xarray DataArrays from the ValueArrays
    da_hist = xr.DataArray(va_hist)
    da_imd = xr.DataArray(va_imd)
    da_merged_ssp245 = xr.DataArray(va_merged_ssp245)
    da_merged_ssp585 = xr.DataArray(va_merged_ssp585)
    df_hist=da_hist.to_dataframe()
    df_imd=da_imd.to_dataframe()
    df_ssp245=da_merged_ssp245.to_dataframe()
    df_ssp585=da_merged_ssp585.to_dataframe()

    # Rename the columns to indicate their source before merging
    df_hist = df_hist.rename(columns={'pr': 'hist'})
    df_imd = df_imd.rename(columns={'pr': 'observed'})
    df_ssp245 = df_ssp245.rename(columns={'pr': 'ssp245'})
    df_ssp585 = df_ssp585.rename(columns={'pr': 'ssp585'})

    # Merge all DataFrames on their common date-time index
    df_hist_imd = df_hist.join([df_imd], how='outer')
    df_ssp245_ssp585 = df_ssp245.join([ df_ssp585], how='outer')
    
    
    # Merge the DataFrames by concatenating them along the rows (time index)
    merged_df = pd.concat([df_hist_imd, df_ssp245_ssp585])
    Data=merged_df.to_csv()
    

    # Save the result to the session (consider using Django cache or database)
    from django.contrib.sessions.models import Session
    try:
        session = Session.objects.get(session_key=session_key)
        session_data = Data
        session_decoded = session.get_decoded()
        session_decoded['processed_data'] = session_data
        session.session_data = Session.objects.encode(session_decoded)
        session.save()
        
        # session_data = session.get_decoded()
        # # session_data[session_key] = context_csv
        # session_data['ppt_view_netcdf_annual'] = {
        #     'Data': Data
        # }
        # session.session_data = session.encode(session_data)
        # session.save()
        
    except Session.DoesNotExist:
        # Handle the case where the session does not exist
        print(f"Session with key {session_key} does not exist.")
    return

@shared_task
def process_csv_task(va_hist_pickle, va_imd_pickle, va_merged_ssp245_pickle, va_merged_ssp585_pickle, session_key):
    va_hist = dill.loads(va_hist_pickle)
    va_imd = dill.loads(va_imd_pickle)
    va_merged_ssp245 = dill.loads(va_merged_ssp245_pickle)
    va_merged_ssp585 = dill.loads(va_merged_ssp585_pickle)
    # Merge all DataFrames on their common date-time index
    df_hist_imd = va_hist.join([va_imd], how='outer')
    df_ssp245_ssp585 = va_merged_ssp245.join([ va_merged_ssp585], how='outer')
    # Merge the DataFrames by concatenating them along the rows (time index)
    merged_df = pd.concat([df_hist_imd, df_ssp245_ssp585])
    Data=merged_df.to_csv()
    

    # Save the result to the session (consider using Django cache or database)
    from django.contrib.sessions.models import Session
    try:
        session = Session.objects.get(session_key=session_key)
        session_data = Data
        session_decoded = session.get_decoded()
        session_decoded['processed_data'] = session_data
        session.session_data = Session.objects.encode(session_decoded)
        session.save()
        
        # session_data = session.get_decoded()
        # # session_data[session_key] = context_csv
        # session_data['ppt_view_netcdf_annual'] = {
        #     'Data': Data
        # }
        # session.session_data = session.encode(session_data)
        # session.save()
        
    except Session.DoesNotExist:
        # Handle the case where the session does not exist
        print(f"Session with key {session_key} does not exist.")
    return