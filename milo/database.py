from peewee import (
    SqliteDatabase,
    Model,
    ForeignKeyField,
    CharField,
    AutoField,
    DateTimeField,
    IntegerField,
)
from milo.loggers import get_loggers

app_logger = get_loggers()

sqlitedb = SqliteDatabase("data/db.sqlite3", pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = sqlitedb


class Franchise(BaseModel):
    name = CharField(unique=True)
    other_names = CharField()


class Game(BaseModel):
    name = CharField(unique=True)
    franchise = ForeignKeyField(Franchise, backref="games")
    other_names = CharField()


class Session(BaseModel):
    id = AutoField()
    name = CharField(null=True)
    start = DateTimeField()
    end = DateTimeField()


class CODMatchType(BaseModel):
    name = CharField()


class CODMatch(BaseModel):
    session = ForeignKeyField(Session, backref="cod_matches")
    discord_usernames = CharField()
    type = ForeignKeyField(CODMatchType, backref="cod_matches")
    score_1 = IntegerField()
    score_2 = IntegerField()


class Platform(BaseModel):
    name = CharField(unique=True)
    other_names = CharField()


class User(BaseModel):
    discord_username = CharField(unique=True)
    platform = ForeignKeyField(Platform, backref="users")
    activision_id = CharField(null=True)
    steam_id = CharField(null=True)


# simple utility function to create tables
def create_tables() -> None:
    with sqlitedb:
        sqlitedb.create_tables(
            [Franchise, Game, Session, CODMatchType, CODMatch, Platform, User]
        )
