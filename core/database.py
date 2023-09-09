import time
import pymongo
import functools
import logging
import copy
import math
from bson.objectid import ObjectId
import json
import logging

from core import core
from . import globalSettings

logger = logging.getLogger(__name__)
logger.setLevel(globalSettings.args.log_level)

db = None
dbClient = None
def initialize(connectionString,database):
    global db
    global dbClient
    dbClient = pymongo.MongoClient(connectionString)
    db = dbClient[database]

def mongoConnectionWrapper(func):
    @functools.wraps(func)
    def wrapper(inst, *args, **kwargs):
        for x in range(1,3):
            try:
                return func(inst, *args, **kwargs)
            except (pymongo.errors.AutoReconnect, pymongo.errors.ServerSelectionTimeoutError) as e:
                logger.debug("PyMongo auto-reconnecting {}".format({ "exception" : e }))
                time.sleep(1)
        logger.warning("PyMongo connection failure")
    return wrapper

class _admin():
    @mongoConnectionWrapper
    def dropCollection(self,collection):
        db[collection].drop()
        return

class _document():
    _id = str()
    _dbCollection = None
    lastUpdateTime = int()

    @mongoConnectionWrapper
    def new(self):
        try:
            self.lastUpdateTime = int(time.time())
            data = core.helpers.classToJson(self)
            del data["_id"]
            result = db[self._dbCollection].insert_one(data)
            if result.inserted_id:
                self._id = str(result.inserted_id)
                return { "_id" : self._id }
        except pymongo.errors.DuplicateKeyError:
            raise core.exceptions.error("Unable to create a new document due to 'Duplicate keys'")
        raise core.exceptions.error("Unknown error occurred while creating a new document")

    @mongoConnectionWrapper
    def get(self,_id,json=False,excludeFields=[],includeJson=False,includeFields=[]):
        query = { "_id" : ObjectId(_id) }
        if includeFields and json:
            includeFields = {field:1 for field in includeFields}
            docs = db[self._dbCollection].find(query,includeFields)
        elif excludeFields and json:
            excludeFields = {field:0 for field in excludeFields}
            docs = db[self._dbCollection].find(query,excludeFields)
        else:
            docs = db[self._dbCollection].find(query)
        logger.debug("Database execution stats {}".format({ "stats" : docs.explain()["executionStats"] }))
        result = None
        resultObject = None
        for doc in docs:
            if json or includeJson:
                result = core.helpers.dbSanitize(doc,reverse=True)
            if not json:
                resultObject = core.helpers.jsonToClass(self,doc)
        if not result and not resultObject:
            raise core.exceptions.error("Unknown error occurred while loading the document")
        if not json and includeJson:
            return result, resultObject
        elif not json:
            return resultObject
        return result

    @mongoConnectionWrapper
    def query(self,query=None,json=False,skip=0,limit=100,sort=None,ascending=True,pageStats=False,excludeFields=[],includeFields=[],includeJson=False):
        if not query:
            query = {}
        order = -1
        if ascending:
            order = 1
        if includeFields and json:
            includeFields = {field:1 for field in includeFields}
            docs = db[self._dbCollection].find(query,includeFields)
        elif excludeFields and json:
            excludeFields = {field:0 for field in excludeFields}
            docs = db[self._dbCollection].find(query,excludeFields)
        else:
            docs = db[self._dbCollection].find(query)
        try:
            if sort:
                if type(sort) is list:
                    docs = docs.sort(sort)
                else:
                    docs = docs.sort(sort,order)
            if skip:
                docs = docs.skip(skip)
            logger.debug("Database execution stats {}".format({ "stats" : docs.explain()["executionStats"] }))
            results = []
            if pageStats:
                docCount = db[self._dbCollection].count_documents(query)
                yield {"total":docCount,"pages":math.ceil(docCount/limit),"pageSize":limit,"skipped":skip}
            for doc in docs:
                _class = copy.copy(self)
                if includeJson:
                    results.append((core.helpers.dbSanitize(doc,reverse=True),core.helpers.jsonToClass(_class,doc)))
                elif json:
                    results.append(core.helpers.dbSanitize(doc,reverse=True))
                else:
                    results.append(core.helpers.jsonToClass(_class,doc))
                if len(results) == limit:
                    if limit == 1:
                        yield results[0]
                    else:
                        yield results
                    results = []
        finally:
            docs.close()
        if len(results) > 0:
            yield results

    @mongoConnectionWrapper
    def querySample(self,query=None,json=False,size=100):
        if not query:
            query = {}
        
        docs = db[self._dbCollection].aggregate(
                [
                    {"$match":query},
                    {"$sample":{"size":size}}
                ]
            )
        try:
            results = []
            for doc in docs:
                _class = copy.copy(self)
                if json:
                    results.append(core.helpers.dbSanitize(doc,reverse=True))
                else:
                    results.append(core.helpers.jsonToClass(_class,doc))

        finally:
            docs.close()
        
        return results

    @mongoConnectionWrapper
    def groupedQuery(self,groupBy,sort="_id",ascending=True,groupLimit=None,query=None,json=False,skip=None,limit=100,pageStats=False):
        if not query:
            query = {}
        order = -1
        if ascending:
            order = 1
        aggregationQuery = []

        if query:
            aggregationQuery.append({"$match":query})

        if sort:
            aggregationQuery.append({"$sort":{sort:order}})

        if groupLimit:
            if groupLimit == 1:
                aggregationQuery.append({"$group":{"_id":f"${groupBy}","docs":{"$first":"$$ROOT"}}})
                aggregationQuery.append({"$replaceRoot":{"newRoot":f"$docs"}})
            else:
                aggregationQuery.append({"$group":{"_id":f"${groupBy}","docs":{"$push":"$$ROOT"}}})
                aggregationQuery.append({'$project': {'docs': {'$slice': ['$docs', groupLimit]}}})
        else:
            aggregationQuery.append({"$group":{"_id":f"${groupBy}","docs":{"$push":"$$ROOT"}}})

        docs = db[self._dbCollection].aggregate(aggregationQuery)

        results = []
        for doc in docs:
            _class = copy.copy(self)
            if json:
                results.append(core.helpers.dbSanitize(doc,reverse=True))
            else:
                results.append(core.helpers.jsonToClass(_class,doc))
            if len(results) == limit:
                break
        docs.close()
        return results

    @mongoConnectionWrapper
    def update(self,fields):
        fields.append("lastUpdateTime")
        self.lastUpdateTime = int(time.time())

        updateData = {}
        for field in fields:
            updateData[field] = getattr(self,field)
        updateData = core.helpers.dbSanitize(updateData)
        result = db[self._dbCollection].update_one({ "_id" : ObjectId(self._id) },{ "$set" : updateData })
        if result.matched_count == 1 and (result.modified_count == 1 or result.raw_result["updatedExisting"] == True):
            return
        raise core.exceptions.error("Document not updated")

    @mongoConnectionWrapper
    def delete(self,query=None):
        if query:
            result = db[self._dbCollection].delete_many(query)
            return
        result = db[self._dbCollection].delete_one({ "_id" : ObjectId(self._id) })
        if result.deleted_count == 1:
            return
        raise core.exceptions.error("Document not deleted")
    
    @mongoConnectionWrapper
    def uniqueCount(self,field,query):
        return len(db[self._dbCollection].distinct(field,query))
    
    def createIndexes(self):
        pass
