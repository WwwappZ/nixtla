from flask import Blueprint, request, jsonify
from nixtla import NixtlaClient
import pandas as pd
from utils import require_apikey
from config import Config

nixtla_forecast_bp = Blueprint('forecast', __name__)

# Initialiseer de NixtlaClient
nixtla_client = NixtlaClient(api_key=Config.NICTLA_APP_ID)

@nixtla_forecast_bp.route('/forecast', methods=['POST'])
@require_apikey
def make_nixtla_forecast():
    data = request.json
    
    # Extract the relevant fields from the JSON input
    sensor_id = data.get('sensor_id')
    naam = data.get('naam')
    soort = data.get('soort')
    sensor_data = data.get('data', [])
    
    # Convert the sensor data to a pandas DataFrame
    df = pd.DataFrame(sensor_data)
    df['datum'] = pd.to_datetime(df['datum'], utc=True)  # Assume input is in UTC
    
    # Sort the dataframe by date
    df = df.sort_values('datum')
    
    if soort != 'temperatuur':
        # Calculate the differences in values to get the changes for non-temperature data
        df['value'] = df['value'].diff().fillna(0)
    
    # Rename the columns to match what Nixtla expects
    df = df.rename(columns={'datum': 'time_col', 'value': 'target_col'})
    
    # Set the index to the date column
    df = df.set_index('time_col')
    
    # Resample the data to hourly frequency
    df = df.resample('1H').mean()
    
    # Forward fill any missing values created by resampling
    df = df.ffill()
    
    # Print debug information
    print("DataFrame after preprocessing:")
    print(df.head())
    
    # Maak een voorspelling voor de komende 24 uur
    try:
        # Verwijder tijd kolom voor de voorspelling
        df.reset_index(inplace=True)
        
        fcst_df = nixtla_client.forecast(df, h=24, level=[80, 90], time_col='time_col', target_col='target_col', freq='1H')
        
        # Zorg ervoor dat de voorspelde tijden ook in UTC zijn
        fcst_df['time_col'] = pd.to_datetime(fcst_df['time_col'], utc=True)
        
        # Converteer de voorspellingen naar de gewenste structuur
        forecast_list = []
        for idx, row in fcst_df.iterrows():
            forecast_list.append({
                'datum': row['time_col'].isoformat(),
                'value': row['TimeGPT']
            })
        
        return jsonify({'forecast': forecast_list}), 200
    except Exception as e:
        print("Error during forecasting:", str(e))
        return jsonify({'error': str(e)}), 400