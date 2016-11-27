
import os
import json
import logging
from datetime import datetime

from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import Proxy, MySQLDatabase, Model
from peewee import CharField, TextField
from peewee import IntegerField, DecimalField
from peewee import DateTimeField


dbproxy = Proxy()


def config_ssl(dirpath):
    """Set up SSL certificates."""

    if os.path.isdir(dirpath):
        logging.info('Using SSL certificates from {}'.format(dirpath))
        ssl = {
            'key': os.path.join(dirpath, 'client-key.pem'),
            'cert': os.path.join(dirpath, 'client-cert.pem'),
            'ca': os.path.join(dirpath, 'ca-cert.pem')
        }
    else:
        ssl = None

    return ssl


def start_database(dbname, sqlite=False, tbl_name=None, **kwargs):
    """Connect to a SQLite or MySQL database.

    Args:
        dbname (str): Database path (SQLite) or name (MySQL).

    Kwargs:
        sqlite (bool): Use SQLite instead of MySQL.
        tbl_name (str): Alternative name for locations table.
        host (str): MySQL host.
        user (str): Username for MySQL.
        passwd (str): Password for MySQL.
        ssl (dict): Dictionary of paths to SSL certificates.
    """
    if sqlite:
        db = SqliteExtDatabase(dbname)
    else:
        db = MySQLDatabase(dbname, **kwargs)

    if tbl_name is not None:
        Location._meta.db_table = tbl_name.strip()

    dbproxy.initialize(db)
    db.create_table(Location, safe=True)

    return db


class BaseModel(Model):
    class Meta:
        database = dbproxy


class JSONField(TextField):
    def db_value(self, value):
        """Convert Python object into value for DB."""
        return json.dumps(value)

    def python_value(self, value):
        """Convert data coming from DB to Python object."""
        if value is None:
            return None
        return json.loads(value)


class Location(BaseModel):
    location = CharField(index=True)
    quality = CharField(null=True)
    state = CharField(null=True)
    city = CharField(null=True)
    county = CharField(null=True)
    country = CharField(null=True)

    lat = DecimalField(null=True, max_digits=12, decimal_places=7)
    lng = DecimalField(null=True, max_digits=12, decimal_places=7)
    accuracy = CharField(null=True)
    confidence = IntegerField(null=True)

    address = TextField(null=True)
    neighborhood = TextField(null=True)
    postal = CharField(null=True)
    bbox = JSONField(null=True)

    content = JSONField(null=True)
    provider = CharField()
    created = DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'locations'
