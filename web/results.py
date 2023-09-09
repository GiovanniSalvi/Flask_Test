import logging

from core import core

logger = logging.getLogger(__name__)
logger.setLevel(core.globalSettings.args.log_level)
    
@core.api.server.route("/results", methods=["GET"])
def resultsPage():
    resultsList = next(core.results._result().query())
    return core.api.render_template("results.html",resultsList=resultsList)