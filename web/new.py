import logging
import json

from core import core

logger = logging.getLogger(__name__)
logger.setLevel(core.globalSettings.args.log_level)
    
@core.api.server.route("/new", methods=["GET"])
def newPage():
    return core.api.render_template("new.html")

@core.api.server.route("/new", methods=["POST"])
def newItem():
    data = json.loads(core.api.request.data)
    core.results._result().new(data["name"],data["type"])
    return { "msg" : "Successful" }, 200