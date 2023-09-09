import cherrypy
from flask import Flask, request, make_response, redirect, g, send_file, render_template, send_from_directory, Blueprint, after_this_request
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import _thread
import logging
import traceback

from . import globalSettings

logger = logging.getLogger(__name__)
logger.setLevel(globalSettings.args.log_level)

base = "/api/1.0/"
server = None

def initialize(name, **kwargs):
	global server
	server = Flask(name,**kwargs)
	server.wsgi_app = ProxyFix(server.wsgi_app)

	@server.errorhandler(Exception)
	def unhandledExceptionHook(e):
		trace = ''.join(traceback.format_exception(type(e), e, e.__traceback__)).replace("\n","\\n")
		logger.error("Uncaught Exception {}".format({ "traceback" : trace }))
		return { "error" : "Unexpected error occurred" }, 500

def startServer(webserverArguments,threaded=False):
	global server
	cherrypy.tree.graft(server.wsgi_app, '/')
	cherrypy.config.update(webserverArguments)
	if threaded:
		_thread.start_new_thread(cherrypy.engine.start, ())
	else:
		cherrypy.engine.start()

