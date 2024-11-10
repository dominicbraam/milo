class FuncHandler:

    def __init__(self, identifier: str, args: dict):
        self.identifier: str = identifier
        self.args: dict = args

        d = "_"
        split_data = self.identifier.split(d)
        self.module = d.join(split_data[:1])
        self.name = d.join(split_data[1:])

    def call_function(self) -> None:

        module = __import__("mods." + self.module, fromlist=["object"])
        func = getattr(module, self.name)
        response = func()

        return response
