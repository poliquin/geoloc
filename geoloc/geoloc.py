#!/usr/bin/env python

import csv
import time
import logging
from collections import OrderedDict

import geocoder
from peewee import DoesNotExist
from us import states
from database import db, Location


PROVIDERS = OrderedDict([  # services to use, in default priority
    ('google', geocoder.google),
    ('bing', geocoder.bing),
    ('yahoo', geocoder.yahoo),
    ('mapquest', geocoder.mapquest),
    ('tomtom', geocoder.tomtom),
    ('here', geocoder.here),
    ('arcgis', geocoder.arcgis)
])
NO_RESULTS = frozenset(['No requests', 'No Geometry', 'ZERO_RESULTS'])


class NoResultError(Exception):
    pass


def save(loc):
    """Add record to database."""
    Location.insert(
        location=loc.location,
        quality=loc.quality,
        state=loc.state,
        city=loc.city,
        county=loc.county,
        country=loc.country,
        lat=loc.lat,
        lng=loc.lng,
        accuracy=loc.accuracy,
        confidence=loc.confidence,
        address=loc.address,
        neighborhood=loc.neighborhood,
        postal=loc.postal,
        bbox=loc.bbox,
        content=loc.content,
        provider=loc.provider
    ).execute()


def lookup(location_name, geo_service='google'):
    func = PROVIDERS[geo_service]
    loc = func(location_name)
    if loc.status == 'OK':
        return loc
    elif loc.status in NO_RESULTS:
        raise NoResultError('No result from server')
    else:
        raise Exception(loc.status)


def build_search(state, place):
    """Combine and normalize place name and state into search."""
    state, place = state.strip(), place.strip().lower()
    if state == '':
        return None, place

    state = states.lookup(state.strip())
    if place.endswith(state.name.lower()):
        # search string contains full state name already
        return state.abbr, place
    elif place.endswith(', ' + state.abbr.lower()):
        # search string contains state abbreviation already
        return state.abbr, place
    else:
        # add state abbreviation to search string
        place = place.strip(',')
        return state.abbr, place + ', ' + state.abbr.lower()


def check_if_exists(location):
    """Check if location already exists in database."""
    try:
        Location.select(Location.id).where(Location.location == location).get()
        return True
    except DoesNotExist:
        return False


def main(infile, outfile='locs.db', provider='google', wait=0.1):
    db.init(outfile)
    db.create_table(Location, safe=True)

    fh = open(infile, 'r')
    rdr = csv.DictReader(fh)
    for search in rdr:
        state, place = search['state'], search['place']
        state, location = build_search(state, place)

        if check_if_exists(location):
            logging.info('Already in database: {0}'.format(location))
            continue

        try:
            loc = lookup(location, provider)
            logging.info('Found result for {0}'.format(location))
        except NoResultError:
            logging.warning('No result for {0}'.format(location))
            continue
        else:
            if state is not None and loc.state != state:
                # search did not return result in correct state
                logging.warning('State for {0} != {1}'.format(location, state))
            save(loc)
        time.sleep(wait)

    db.close()


if __name__ == "__main__":
    import argparse
    argp = argparse.ArgumentParser(description='Geocode locations')
    argp.add_argument('infile', help='Input source')
    argp.add_argument('outfile', nargs='?', default='locs.db',
                      help='Output database')
    argp.add_argument('-v', '--verbose', action='store_true', help='Logging on')
    argp.add_argument('-w', '--wait', type=float, default=0.1,
                      help='Wait (in seconds) between requests to provider')
    argp.add_argument('-p', '--provider', default='google', help='Use provider')

    opts = argp.parse_args()
    if opts.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s|%(levelname)s|%(name)s| %(message)s'
        )
        logging.getLogger('requests').setLevel(logging.WARNING)

    wait = max(0, opts.wait)  # ignore negative wait times
    main(opts.infile, opts.outfile, opts.provider, wait)
