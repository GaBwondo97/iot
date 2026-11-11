-- CityPulse AI — Seed Reference Data: Cities
-- Idempotent: safe to re-run. Uses ON CONFLICT DO NOTHING.
-- Aligned with Person 2 City & Area Registry (city_id = lowercase hyphenated slug).

INSERT INTO cities (city_code, name, country_code, latitude, longitude)
VALUES
    ('kuala-lumpur', 'Kuala Lumpur', 'MY', 3.139000, 101.686855),
    ('london',       'London',       'GB', 51.507400, -0.127800),
    ('tokyo',         'Tokyo',        'JP', 35.689500, 139.691700)
ON CONFLICT (city_code) DO NOTHING;
