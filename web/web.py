import time
from pathlib import Path

from core import core

def load():
    serverSettings = {
        "server.socket_host" : core.globalSettings.args.bind_address,
        "server.socket_port" : core.globalSettings.args.bind_port,
        "engine.autoreload.on" : False    
    }
    core.api.initialize("webAPI",template_folder=str(Path("web","build")),static_folder=str(Path("web","build","static")))
    core.api.base = "/api/1.0/"

    core.database.initialize(core.globalSettings.args.database_url,core.globalSettings.args.database)

    from . import index, results, new

    if core.globalSettings.args.autoreload:
        @core.api.server.before_request
        def reload():
            core.api.server.jinja_env.cache = {}

    core.api.startServer(serverSettings,True)

    while True:
        time.sleep(60)