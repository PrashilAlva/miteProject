from pymongo import MongoClient

client=MongoClient()

db=client.dhi_analytics

collections=db["dhi_internal"]

def get_academic_year():
    data=collections.aggregate([
        {"$group":{"_id":"$academicYear"}},
        {"$project":{"AcademicYear":"$_id","_id":0}}
    ])
    return [i for i in data]