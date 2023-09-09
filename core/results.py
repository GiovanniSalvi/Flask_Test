import logging

from core import core

logger = logging.getLogger(__name__)
logger.setLevel(core.globalSettings.args.log_level)

class _result(core.database._document):
    name = str()
    mainType = str()

    _dbCollection = "results"

    def new(self,name,mainType):
        self.name = name
        self.mainType = mainType
        return super(_result, self).new()
    