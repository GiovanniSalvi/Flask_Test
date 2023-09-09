import logging

from core import core

logger = logging.getLogger(__name__)
logger.setLevel(core.globalSettings.args.log_level)
    
@core.api.server.route("/", methods=["GET"])
def indexPage():
    return core.api.render_template("index.html")