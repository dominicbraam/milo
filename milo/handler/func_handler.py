from discord import Message
from milo.loggers import get_loggers

app_logger = get_loggers()


class FuncHandler:

    def __init__(self, message: Message, identifier: str, args: dict):
        self.message = message
        self.modules_loc = "milo.mods"
        self.identifier: str = identifier
        self.args: dict = args

        d = "_"
        split_data = self.identifier.split(d)
        self.module = split_data[0]
        self.class_name = split_data[1]
        self.name = d.join(split_data[2:])

    def call_function(self) -> None:

        module = __import__(
            f"{self.modules_loc}.{self.module}", fromlist=["object"]
        )
        class_obj = getattr(module, self.class_name)(self.message, self.args)
        response = getattr(class_obj, self.name)()

        return response

    def get_module(self) -> str:
        return self.module
