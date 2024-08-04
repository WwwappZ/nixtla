# Gebruik een officiële Python runtime als parent image
FROM python:3.9-slim

# Stel de werkdirectory in de container in
WORKDIR /app

# Kopieer de requirements file in de container
COPY requirements.txt ./

# Installeer de benodigde packages
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode naar de container
COPY . .

# Geef het commando om de app te draaien met Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:3012", "app:app"]