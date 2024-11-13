from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

sqlitedb = SqliteDatabase("data/db/db.sqlite3", pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = sqlitedb


class Settings(BaseModel):
    server_id = IntegerField(unique=True)
    settings = TextField()


class Franchise(BaseModel):
    name = CharField(unique=True)
    other_names = CharField()


class Game(BaseModel):
    name = CharField(unique=True)
    franchise = ForeignKeyField(Franchise, backref="games")
    other_names = CharField()


class Session(BaseModel):
    name = CharField(null=True)
    start = DateTimeField()
    end = DateTimeField(null=True)


class CODMatchType(BaseModel):
    name = CharField()


class CODMatch(BaseModel):
    session = ForeignKeyField(Session, backref="cod_matches")
    discord_user_ids = CharField()
    type = ForeignKeyField(CODMatchType, backref="cod_matches")
    score_1 = IntegerField()
    score_2 = IntegerField()


class Platform(BaseModel):
    name = CharField(unique=True)
    other_names = CharField()


class Person(BaseModel):
    discord_id = IntegerField()
    activision_id = CharField(null=True)
    steam_id = CharField(null=True)
    platform = ForeignKeyField(Platform, backref="persons")


tables = [
    Settings,
    Franchise,
    Game,
    Session,
    CODMatchType,
    CODMatch,
    Platform,
    Person,
]
