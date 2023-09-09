import logging
import argparse
import os
import sys
import _thread
import time
from traceback import format_exception

try:
    if "/" in sys.argv[0]:
        os.chdir("/".join(sys.argv[0].split("/")[:-1]))
except:
    pass

# Setup logging and un-handled exception hook
logging.basicConfig(format="%(asctime)s lab1 %(levelname)s %(name)s[%(process)d] %(filename)s:%(lineno)d | %(message)s")
logger = logging.getLogger(__name__)

def unhandledExceptionHook(*exc_info):
    message = ''.join(format_exception(*exc_info)).replace("\n","\\n")
    logger.critical(f"Uncaught Exception {message}")

sys.excepthook = unhandledExceptionHook

mainParser = argparse.ArgumentParser(add_help=False)
mainParser.add_argument('--database_url', type=str, default="mongodb://127.0.0.1", help='--database_url mongodb://127.0.0.1')
mainParser.add_argument('--database', type=str, default="lab1", help='--database lab1')
mainParser.add_argument('--log_level', type=str, default="WARNING", help='log_level WARNING')
subParsers = mainParser.add_subparsers(help='commands')

webParser = subParsers.add_parser('web', parents=[mainParser])
webParser.add_argument('--bind_address', type=str, default="127.0.0.1", help='--bind_address 127.0.0.1')
webParser.add_argument('--bind_port', type=int, default=5015, help='--bind_port 5015')
webParser.add_argument('--autoreload', type=bool, default=False, help='Flag to enable autoreload', nargs="?", const=True)
webParser.set_defaults(component='web')

args = mainParser.parse_args()
from core import globalSettings
globalSettings.args = args

if hasattr(args,"component"):
    logger.setLevel(globalSettings.args.log_level)
    logger.debug(f"args={globalSettings.args}")
    
    if args.component == "web":
        from web import web
        web.load()
else:
    mainParser.print_help()
