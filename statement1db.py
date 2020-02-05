from pymongo import MongoClient

client=MongoClient()

db=client.dhi_analytics

collections=db["dhi_internal"]

def get_academic_year():
    collections=db["dhi_internal"]
    data=collections.aggregate([
        {"$group":{"_id":"$academicYear"}},
        {"$project":{"AcademicYear":"$_id","_id":0}}
    ])
    return [i for i in data]


def get_semester():
    collections=db["dhi_internal"]
    data=collections.find({})
    dataa=list()
    for ele in data:
        dataa.append(ele)
    container=set()
    for ele in dataa:
        container.add(ele["departments"][0]["termNumber"])
    container=sorted(container)
    return container


def placement(name):
    collections=db["pms_placement_student_details"]
    val=collections.find({})
    data=list()
    placed=list()
    for ele in val:
        data.append(ele)
    for ele in range(0,len(data)):
        cont=data[ele]["studentList"]
        for stud in cont:
            if name==stud["studentName"]:
                comp=data[ele]["companyName"]
                sal=data[ele]["salary"]
                placed.append({"company":comp,"role":"Software Engineer","salary":sal})
    return placed
        
def demo(email):
    collections = db["dhi_user"]
    data=collections.find({"email":email})
    for ele in data:
        return placement(ele["name"])



demo("mr.kirankumar4u@gmail.com")




        