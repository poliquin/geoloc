Geocode Location Names
======================

Uses the Python `geocoder` library to geocode a set of locations and
saves search results to a SQLite database. The script handles the
following:

1. Reading text or CSV input with state and location name
2. Comparing search with records already in database
3. Spacing requests to geocoding service for new locations
4. Saving responses to SQLite

## Running the Program

The input file should be CSV with `state` and `place` columns. It should
be something like:

    state,place
    ok,oklahoma city
    in,indianapolis
    co,"colorado springs, co"

The program will combine the place and state name to create a query for
the geocoder; it ensures the state is not already in the place.

Run a file of queries like this:

    ./geoloc/geoloc.py places_to_search.csv locs.db -v -w 0.2

The above reads searches from `places_to_search.csv` and loads results into
a SQLite database called `locs.db`. It waits 0.2 seconds between requests
and provides detailed log output (per the `-v` flag). The default geocoding 
provider is Google, but this can be changed with the `-p` flag.
