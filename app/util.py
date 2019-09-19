from bson.json_util import dumps
from bson.objectid import ObjectId


def dump(result):
    return dumps(result, ensure_ascii=False)

def getId(result):
    return dumps(result, ensure_ascii=False)