#!/usr/bin/env python

from __future__ import absolute_import

import csv
import re
import time
import logging
from collections import OrderedDict

import geocoder
from peewee import DoesNotExist
from us import states
from .database import start_database, config_ssl, Location


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
OVER_LIMIT = frozenset(['OVER_QUERY_LIMIT'])


class NoResultError(Exception):
    pass


class QueryLimitError(Exception):
    pass


def save(loc, meta_id=None):
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
        provider=loc.provider,
        meta_id=meta_id
    ).execute()


def lookup(location_name, geo_service='google'):
    func = PROVIDERS[geo_service]
    loc = func(location_name)
    if loc.status == 'OK':
        return loc
    elif loc.status in NO_RESULTS:
        raise NoResultError('No result from server')
    elif loc.stats in OVER_LIMIT:
        raise QueryLimitError('Over query limit')
    else:
        raise Exception(loc.status)


def build_search(state, place):
    """Combine and normalize place name and state into search."""
    state, place = state.strip(), place.strip().lower()
    if state == '':
        return None, place

    place = re.sub(r'^close to\s*', '', place)

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


def check_if_exists(location=None, meta_id=None):
    """Check if location already exists in database."""

    if location is None and meta_id is None:
        return False

    try:
        Location.select(Location.id).where(
            ((Location.location == location) | (location is None)) &
            ((Location.meta_id == meta_id) | (meta_id is None))
        ).get()
        return True
    except DoesNotExist:
        return False


def main(infile, db, meta=None, build=False, delim=',', provider='google',
         wait=0.1):
    """Run the geocoder."""

    fh = open(infile, 'r')
    rdr = csv.DictReader(fh, delimiter=delim)

    for search in rdr:
        if build:
            state, place = search['state'], search['place']
            state, location = build_search(state, place)
        else:
            location = search['location'].strip()

        meta_id = int(search[meta]) if meta is not None else None

        if check_if_exists(location, meta_id):
            logging.debug('Already in database: {0}'.format(location))
            continue

        try:
            loc = lookup(location, provider)
            logging.info('Found result for {0}'.format(location))
        except NoResultError:
            logging.warning('No result for {0}'.format(location))
            continue
        except QueryLimitError:
            logging.critical('Over query limit!')
            break
        except Exception as err:
            logging.error(err)
            continue
        else:
            if build and state is not None and loc.state != state:
                # search did not return result in correct state
                logging.warning('State for {0} != {1}'.format(location, state))

            save(loc, meta_id)
        time.sleep(wait)


def open_db(dbname, tbl='locations', host='127.0.0.1', user='root',
            pwd=None, ssl=None):
    """Create connection to database."""

    return start_database(
        dbname,
        sqlite='.' in dbname or host is None,
        tbl_name=tbl,
        host=host,
        user=user,
        passwd=pwd,
        ssl=config_ssl(ssl) if ssl is not None else None
    )


if __name__ == "__main__":
    import argparse
    argp = argparse.ArgumentParser(description='Geocode locations')
    argp.add_argument('infile', help='Input source')
    argp.add_argument('dbname', nargs='?', default='locs.db',
                      help='Output database')
    argp.add_argument('--meta', help='Input column with arbitrary location ID')
    argp.add_argument('--tbl', default='locations', help='Table name')
    argp.add_argument('-t', '--tabs', action='store_true', help='Tab delimit')
    argp.add_argument('-v', '--verbose', action='store_true', help='Log on')
    argp.add_argument('-w', '--wait', type=float, default=0.1,
                      help='Wait (in seconds) between requests to provider')
    argp.add_argument('-p', '--provider', default='google', help='Provider')
    argp.add_argument('-d', '--dev', action='store_true', help='Development')
    argp.add_argument('-b', '--build', action='store_true',
                      help='Create search from state and place columns')
    argp.add_argument('--hst', default=None, help='MySQL host')
    argp.add_argument('--usr', default=None, help='MySQL user')
    argp.add_argument('--pwd', default=None, help='MySQL pass')
    argp.add_argument('--ssl', default='/etc/mysql-ssl', help='SSL certs')

    opts = argp.parse_args()
    if opts.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s|%(levelname)s|%(name)s| %(message)s'
        )
        logging.getLogger('requests').setLevel(logging.WARNING)

    db = open_db(opts.dbname, opts.tbl, opts.hst, opts.usr, opts.pwd, opts.ssl)

    if not opts.dev:
        wait = max(0, opts.wait)  # ignore negative wait times
        delim = '\t' if opts.tabs else ','
        main(opts.infile, db, opts.meta, opts.build, delim,
             opts.provider, wait)
        db.close()
