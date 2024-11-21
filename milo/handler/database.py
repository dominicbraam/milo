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


class SettingsServer(BaseModel):
    reminder_time = IntegerField()

    class Meta:
        table_name = "settings_server"

    units = {
        "reminder_time": "mins",
    }

    # TODO: test with fields with no units
    def get_unit(self, field_name):
        if hasattr(self, field_name):
            unit = self.units.get(field_name, "")
            return unit
        else:
            raise ValueError("Invalid field name")

    # TODO: test with fields with no units
    def get_value_with_unit(self, field_name):
        if hasattr(self, field_name):
            value = getattr(self, field_name)
            unit = self.units.get(field_name, "")
            return f"{value} {unit}"
        else:
            raise ValueError("Invalid field name")


class Session(BaseModel):
    name = CharField(null=True)
    start = DateTimeField()
    end = DateTimeField(null=True)

    class Meta:
        table_name = "session"


class GameFranchise(BaseModel):
    name = CharField(unique=True)
    other_names = CharField()

    class Meta:
        table_name = "game_franchise"


class Game(BaseModel):
    name = CharField(unique=True)
    franchise = ForeignKeyField(GameFranchise, backref="games")
    other_names = CharField()

    class Meta:
        table_name = "game"


class GameMatchType(BaseModel):
    name = CharField()
    game = ForeignKeyField(Game, backref="game_match_types")

    class Meta:
        table_name = "game_match_type"


class GameMatch(BaseModel):
    session = ForeignKeyField(Session, backref="cod_matches")
    game_match_type = ForeignKeyField(GameMatchType, backref="cod_matches")
    match_data = TextField

    class Meta:
        table_name = "game_match"


class GamePlatform(BaseModel):
    name = CharField(unique=True)
    digital_game_service = CharField()

    class Meta:
        table_name = "game_platform"


class Person(BaseModel):
    discord_id = IntegerField()
    activision_id = CharField(null=True)
    steam_id = CharField(null=True)
    platform = ForeignKeyField(GamePlatform, backref="persons")

    class Meta:
        table_name = "person"


tables = [
    SettingsServer,
    Session,
    GameFranchise,
    Game,
    GameMatchType,
    GameMatch,
    GamePlatform,
    Person,
]
