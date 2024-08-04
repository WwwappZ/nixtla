from flask import Flask
from config import Config
from routes import forecast_bp, forecast_weather_bp  # Verander dit van 'forecast' naar 'forecast_bp'

app = Flask(__name__)
app.config.from_object(Config)

# Register blueprints
app.register_blueprint(forecast_bp)  # Gebruik 'forecast_bp' in plaats van 'forecast'
app.register_blueprint(forecast_weather_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3012, debug=True)