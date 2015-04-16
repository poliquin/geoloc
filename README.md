Convert Location Names to Latitude/Longitude
============================================

Uses the Python `geocoder` library to geocode a set of locations
and saves search results to a SQLite database. The script handles
the following:

1. Reading text or CSV input with location names
2. Comparing names with points already in database
3. Spacing requests to geocoding services for new locations
4. Trying failed requests with a different service
5. Saving responses to SQLite

