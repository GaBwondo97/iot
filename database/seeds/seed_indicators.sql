-- CityPulse AI — Seed Reference Data: Environmental Indicators
-- Idempotent: safe to re-run. Uses ON CONFLICT DO NOTHING.
-- Aligned with Person 2 Canonical Data Schema Proposal (Metric Registry).

INSERT INTO environmental_indicators (indicator_code, category, name, unit, description)
VALUES
    -- Weather
    ('temperature',        'weather', 'Temperature',        '°C',        'Air temperature at 2m'),
    ('humidity',           'weather', 'Humidity',           '%',         'Relative humidity at 2m'),
    ('rainfall',           'weather', 'Rainfall',           'mm_per_hour','Precipitation rate'),
    ('wind_speed',         'weather', 'Wind Speed',         'km_per_hour','Wind speed at 10m'),

    -- Air Quality
    ('pm25',               'air_quality', 'PM2.5',        'µg/m³',     'Fine particulate matter'),
    ('pm10',               'air_quality', 'PM10',         'µg/m³',     'Coarse particulate matter'),
    ('aqi',                'air_quality', 'Air Quality Index', 'index',  'AQI score (0-500)'),
    ('co2',                'air_quality', 'CO2',          'ppm',       'Carbon dioxide concentration'),

    -- Traffic
    ('vehicle_count',      'traffic', 'Vehicle Count',     'vehicles',  'Vehicles in observation window'),
    ('average_speed',      'traffic', 'Average Speed',      'km_per_hour','Mean traffic speed'),
    ('traffic_density',    'traffic', 'Traffic Density',    'vehicles_per_km', 'Vehicles per km'),
    ('congestion_level',   'traffic', 'Congestion Level',   'category',  'Congestion: low, medium, high'),

    -- Population
    ('estimated_population','population', 'Estimated Population', 'people', 'Estimated people in area'),
    ('population_density', 'population', 'Population Density', 'people_per_km2', 'People per km²'),
    ('crowd_density',      'population', 'Crowd Density',      'category',  'Crowd: low, medium, high'),
    ('population_change',  'population', 'Population Change',  'people',    'Change in population count')
ON CONFLICT (indicator_code) DO NOTHING;