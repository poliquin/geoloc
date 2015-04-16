#!/usr/bin/env python

import time
from collections import OrderedDict
import geocoder

PROVIDERS = OrderedDict([  # services to use, in default priority
    ('google', geocoder.google),
    ('bing', geocoder.bing),
    ('yahoo', geocoder.yahoo),
    ('mapquest', geocoder.mapquest),
    ('tomtom', geocoder.tomtom),
    ('here', geocoder.here),
    ('arcgis', geocoder.arcgis)
])


class NoResultError(Exception):
    pass


def lookup(location_name, geo_service):
    func = PROVIDERS[geo_service]
    loc = func(location_name)
    if loc.status == 'OK':
        # TODO: put together response for saving to DB
        pass
    elif 'No results' in loc.status or 'No Geometry' in loc.status:
        # TODO: note which services return no result for which locations
        raise NoResultError('No result from server')
    else:
        raise Exception(loc.status)


def main(options):
    pass


if __name__ == "__main__":
    import sys
    import argparse
    argp = argparse.ArgumentParser(description='Geocode locations')
    argp.add_argument('infile', default=sys.stdin, help='Input source')
    argp.add_argument('outfile', default='locs.db', help='Output database')
    argp.add_argument('-p', '--providers', help='Limit used service providers')
    options = argp.parse_args()
