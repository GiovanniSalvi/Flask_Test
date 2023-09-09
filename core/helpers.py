from bson.objectid import ObjectId
import datetime
import os
import base64
import hashlib
import random
import json
import time
import re
import string
import secrets
from pathlib import Path
import logging

from . import globalSettings

logger = logging.getLogger(__name__)
logger.setLevel(globalSettings.args.log_level)

emailRegex = re.compile(r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")
baseDir = os.getcwd()

def jsonToClass(_class,json,reverse=True):
    members = [attr for attr in dir(_class) if not callable(getattr(_class, attr)) and attr and ( attr[0] != "_" or attr == "_id" ) ]
    for member in members:
        foundAndSet = False
        for key, value in json.items():
            if key == member:
                if type(getattr(_class,member)) == type(value):
                    setattr(_class,member,value)
                    foundAndSet = True
                    break
                elif type(getattr(_class,member)) == str or type(getattr(_class,member)) == ObjectId:
                    setattr(_class,member,str(value))
                    foundAndSet = True
                    break
                elif type(getattr(_class,member)) == float and type(value) == int:
                    setattr(_class,member,float(value))
                    foundAndSet = True
                    break
                elif type(getattr(_class,member)) == int and type(value) == float:
                    setattr(_class,member,int(value))
                    foundAndSet = True
                    break
        if not foundAndSet and type(getattr(_class,member)) in [list,dict]:
            setattr(_class,member,type(getattr(_class,member))())
    return dbSanitize(_class,reverse=reverse)

def classToJson(_class,reverse=False):
    members = [attr for attr in dir(_class) if not callable(getattr(_class, attr)) and attr and ( attr[0] != "_" or attr == "_id" ) ]
    result = {}
    for member in members:
        result[member] = getattr(_class,member)
    return dbSanitize(result,reverse=reverse)

def classListToJson(classList):
    results = []
    for _class in classList:
        results.append(classToJson(_class,reverse=True))
    return results

def dbSanitize(value,reverse=False):
    validTypes = [str,int,bool,float,list,dict,None,datetime,ObjectId]
    def dbSanitizeDict(dictValue):
        result = {}
        for key, value in dictValue.items():
            if ("$" in key or "." in key) and not reverse:
                key = key.replace(".","\\u002E").replace("$","\\u0024")
            elif ("\\u002E" in key or "\\u0024" in key) and reverse:
                key = key.replace("\\u002E",".").replace("\\u0024","$")
            if type(value) is dict:
                result[key] = dbSanitizeDict(value)
            elif type(value) is list:
                result[key] = dbSanitizeList(value)
            elif type(value) in validTypes:
                if type(value) is ObjectId:
                    value = str(value)
                elif type(value) is datetime:
                    value = value.timestamp()
                result[key] = value
            else:
                result[key] = str(type(value))
        return result
    def dbSanitizeList(listValue):
        result = []
        for item in listValue:
            if type(item) is dict:
                result.append(dbSanitizeDict(item))
            elif type(item) is list:
                result.append(dbSanitizeList(item))
            elif type(item) in validTypes:
                if type(item) is ObjectId:
                    item = str(item)
                elif type(item) is datetime:
                    item = item.timestamp()
                result.append(item)
            else:
                result.append(str(type(item)))
        return result
    if type(value) is dict:
        return dbSanitizeDict(value)
    elif type(value) is list:
        return dbSanitizeList(value)
    return value

def safeFilepath(filename,basePath=""):
    base = os.path.join(Path("{0}/{1}".format(baseDir,basePath)),'')
    return not os.path.commonprefix((os.path.abspath(Path(filename)),base)) != base
            
def tryValue(dict,key,default=None,matchType=False):
    try:
        if matchType and default != None:
            value = dict[key]
            if type(value) != type(default):
                return default
            else:
                return value
        else:
            return dict[key]
    except:
        return default
