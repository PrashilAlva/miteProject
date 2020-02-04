from bson import ObjectId
from flask.json import JSONEncoder

class MongoJSONEncoder(JSONEncoder):
    def default(self,o):
        if isinstance(o,ObjectId):
            return str(o)