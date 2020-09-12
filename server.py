import json
from pyfs import filetypes, filesystem

with open("settings.json", "r") as s:
    settings = json.load(s)

state = {}

class AtkFile(filetypes.File):
    def __init__(self, *args):
        super().__init__(*args)

    def write(self, val) -> int:
        # write to state
        state[self.name] = val
        return 0

    def read(self):
        # return the entire state of everything in json
        return json.dumps(state)

    def close(self):
        global state
        if self.name in state:
            del state[self.name]

if __name__ == '__main__':
    server = filesystem.FileSystemUDPServer(settings["port"])
    server.start()
