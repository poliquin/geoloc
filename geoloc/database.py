
import json
from datetime import datetime

from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import Model
from peewee import CharField, TextField
from peewee import IntegerField, DecimalField
from peewee import DateTimeField


db = SqliteExtDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db


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
    location = CharField()
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
