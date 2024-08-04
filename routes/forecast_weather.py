import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from nixtla import NixtlaClient
import pandas as pd
from utils import require_apikey
from config import Config

nixtla_forecast_bp = Blueprint('forecast_weather', __name__)

nixtla_client = NixtlaClient(api_key=Config.NICTLA_APP_ID)


@nixtla_forecast_bp.route('/forecast_weather', methods=['POST'])
@require_apikey
def make_nixtla_forecast():
    # Sla de ontvangen data op in een bestand
    data = request.json
  
    soort = data.get('soort')
    sensor_data = data.get('data', [])
    outdoor_temp_data = data.get('outdoor_temp', [])

    # Verwerk sensordata
    df = pd.DataFrame(sensor_data)
    df['datum'] = pd.to_datetime(df['datum'], utc=True)
    df = df.sort_values('datum')

    if soort != 'temperatuur':
        df['value'] = df['value'].diff().fillna(0)

    # Hernoem kolommen en zet index
    df = df.rename(columns={'datum': 'ds', 'value': 'target_col'})
    df = df.set_index('ds')

    # Resample the data to hourly frequency
    df = df.resample('1h').mean()

    # Forward fill any missing values created by resampling
    df = df.ffill()

    # Verwerk buitentemperatuurdata
    outdoor_df = pd.DataFrame(outdoor_temp_data)
    outdoor_df['datum'] = pd.to_datetime(outdoor_df['datum'], utc=True)
    outdoor_df = outdoor_df.sort_values('datum')
    outdoor_df['value'] = pd.to_numeric(outdoor_df['value'], errors='coerce')
    outdoor_df = outdoor_df.dropna()

    outdoor_df = outdoor_df.rename(
        columns={'datum': 'ds', 'value': 'outdoor_temp'})
    outdoor_df = outdoor_df.set_index('ds')

    # Resample naar uurlijkse frequentie
    outdoor_df = outdoor_df.resample('1h').mean()
    outdoor_df = outdoor_df.ffill()

    # Combineer de twee DataFrames
    combined_df = df.join(outdoor_df, how='outer')
    # Vul ontbrekende waarden in beide richtingen
    combined_df = combined_df.ffill().bfill()

    try:
        # Reset de index
        combined_df = combined_df.reset_index(inplace=True)
        df.reset_index(inplace=True)

        fcst_df = nixtla_client.forecast(df=df, X_df=combined_df, h=24, level=[80, 90],
                                         time_col='ds', target_col='target_col', freq='1h')

        # Zorg ervoor dat de voorspelde tijden ook in UTC zijn
        fcst_df['ds'] = pd.to_datetime(fcst_df['ds'], utc=True)

        # Converteer de voorspellingen naar de gewenste structuur
        forecast_list = []
        for idx, row in fcst_df.iterrows():
            forecast_list.append({
                'datum': row['ds'].isoformat(),
                'value': row['TimeGPT']
            })

        return jsonify({'forecast': forecast_list}), 200
    except Exception as e:
        print("Error during forecasting:", str(e))
        return jsonify({'error': str(e)}), 400
