from pymongo import MongoClient
from pprint import pprint

db = MongoClient()
mydb = db.dhi_analytics
dhi_internal = mydb['dhi_internal']
dhi_term_details = mydb['dhi_term_detail']
dhi_student_attendance = mydb['dhi_student_attendance']
dhi_university_details=mydb['pms_university_exam']
dhi_user=mydb['dhi_user']


def getacademicYear():
    academicYear = dhi_internal.aggregate([{"$group":{"_id":"null",
    "academicYear":{"$addToSet":"$academicYear"}}},{"$project":{"academicYear":"$academicYear","_id":0}}])
    for year in academicYear:
        year = year['academicYear']
    return year

def get_term_numbers():
    terms_numbers = dhi_term_details.aggregate([ 
        { "$unwind":"$academicCalendar"}, 
        {"$group":{"_id":"null","termNumber":{"$addToSet":"$academicCalendar.termNumber"}}},
        {"$project":{"_id":0}}
    ])
    for term in terms_numbers:
        terms = term['termNumber']
    terms.sort()
    return terms

def getDept():
    dept=dhi_university_details.find({})
    departments=list()
    for ele in dept:
        if ele["deptId"] not in departments:
            departments.append(ele["deptId"])
    departments.sort(reverse=False)
    return departments

def faculties(year,term,dept):
    collections=dhi_user.find({})
    faculties=list()
    for ele in collections:
        if ele['roles'][0]['roleName']=='FACULTY':
            if ele["employeeGivenId"].startswith(dept):
                faculties.append({"employeeGivenId":ele["employeeGivenId"],"name":ele["name"]})
    # print(faculties)
    return faculties

def placement(usn):
    collections=mydb["pms_placement_student_details"]
    val=collections.find({})
    data=list()
    placed=list()
    for ele in val:
        data.append(ele)
    for ele in range(0,len(data)):
        cont=data[ele]["studentList"]
        for stud in cont:
            if usn==stud["regNo"]:
                comp=data[ele]["companyName"]
                sal=data[ele]["salary"]
                placed.append({"company":comp,"role":"Software Engineer","salary":sal})
    return placed
    #return placed
        
def demo(email):
    collections = mydb["dhi_user"]
    data=collections.find({"email":email})
    for ele in data:
        return placement(ele["usn"])

#demo('kiranapai97@gmail.com')


def get_ia_details(usn,courseCode,section,termNumber,deptId,year):
    ia_percent = 0
    avg_ia_score = 0

    ia_details =[x for x in dhi_internal.aggregate([
        {
        '$unwind': '$studentScores'
        },
        {'$unwind': '$departments'},
        {'$unwind':'$studentScores.evaluationParameterScore'},
        {
            '$match':
            {
                'studentScores.usn':usn,
                'academicYear':year,
                'courseCode':courseCode ,
                'studentScores.section': section,
                'departments.deptId': deptId,
                'studentScores.termNumber': termNumber
            }
        
        },

        {
            '$group':
            {
                '_id':'$iaNumber',
                "maxMarks":{"$addToSet":"$studentScores.evaluationParameterScore.maxMarks"},
                "iaNumber":{"$addToSet":"$iaNumber"},
                "obtainedMarks":{"$addToSet":"$studentScores.totalScore"},
                 "startTime":{"$addToSet":"$startTime"}
            }
        },
        {'$unwind':'$maxMarks'},
        {'$unwind':'$iaNumber'},
        {'$unwind':'$startTime'},
         {'$unwind':'$obtainedMarks'},
        {
            "$project":
                {
                    "_id":0,
                    "maxMarks":"$maxMarks",
                    "obtainedMarks":"$obtainedMarks",
                     "startTime":"$startTime",
                    "iaNumber":"$iaNumber"
                }
        }

    ])]
    for x in ia_details:
        ia_percent = 0
        try:
            ia_percent += (x['obtainedMarks'])
            ia_percent = (x['obtainedMarks']/x['maxMarks'])*100
            ia_percent =  round(ia_percent,2)
            x['ia_percent'] = ia_percent
            avg_ia_score = avg_ia_score + ia_percent
        except ZeroDivisionError:
            avg_ia_score = 0
    
    try:
        avg_ia_score = avg_ia_score/len(ia_details)
        avg_ia_score = round(avg_ia_score,2)
        print(ia_details,avg_ia_score)
        return ia_details,avg_ia_score

    except ZeroDivisionError:
        return ia_details,0

stud = set()        # set of usn
placed = set()          # set of placed
tot_placed = 0
tot_usn = 0

def getAvgMarks(year,subcode,faccode):
    students=list()
    totalMarks=0
    maxMarks=0
    avg=0
    
    collections=dhi_internal.find({'courseCode':subcode})
    for ele in collections:
        if ele['academicYear']==year and ele['faculties'][0]['facultyGivenId']==faccode:
            students.append(ele['studentScores'])
    for i in range(0,len(students)):
        for j in range(0,len(students[i])):
            totalMarks=totalMarks+students[i][j]['evaluationParameterScore'][0]['obtainedMarks']
            maxMarks=maxMarks+students[i][j]['evaluationParameterScore'][0]['maxMarks']
            stud.add(students[i][j]['usn'])

    if maxMarks==0:
        avg=0
    else:
        avg=(totalMarks/maxMarks)*100

    print(stud)

    lst = []
    collections = mydb["pms_placement_student_details"]
    for data in collections.aggregate([{'$group':{'_id':'$studentList.regNo'}}]):
        lst.append(data['_id'])
    
    for usns in lst:
        for i in usns:
            placed.add(i)
    z = placed.intersection(stud) 
    tot_placed = len(z)
    tot_usn = len(stud)
    print(tot_placed,tot_usn)
    try:
        placedPerc = (tot_placed/tot_usn)*100
    except:
        placedPerc = 0
    return avg,placedPerc,tot_placed,tot_usn

def Count(stud):
    c = 0
    collections = mydb["pms_placement_student_details"]
    for st in stud:
        c += collections.find({"studentList.regNo":st}).count()         # offers count
    return c
            
def getSubjects(year,sem,id):
    subjects=list()
    for data in dhi_internal.aggregate([
        {'$match':{'faculties.facultyGivenId':id,'academicYear':year,'departments.termNumber':sem}}
    ]):
        avg,placed_avg,tot_placed,tot_usn = getAvgMarks(year,data['courseCode'],id)
        if {'courseName':data['courseName'],'courseCode':data['courseCode'],'iaAvg':avg,'placementAvg':placed_avg} not in subjects:
            subjects.append({'courseName':data['courseName'],'courseCode':data['courseCode'],'iaAvg':avg,'placementAvg':placed_avg})
    print(subjects)
    return subjects


def getInternal(year,term,empid):
    collections=dhi_internal.find({})
    lst=list()
    placement=list()
    for ele in collections:
        obtained=0
        max=0
        flag = 0
        if ele['faculties'][0]['facultyGivenId']==empid and ele['departments'][0]['termNumber']==term:
            flag = 1
            for item in ele['studentScores']:
                obtained=obtained+item['evaluationParameterScore'][0]['obtainedMarks']
                max=max+item['evaluationParameterScore'][0]['maxMarks']
            obtained=obtained//len(ele['studentScores'])
            max=max//len(ele['studentScores']) 
            lst.append({'subname':ele['courseName'],'iaNum':ele['iaNumber'],'maxMarks':max,'obtainedMarks':obtained})
        if flag == 1:
            a,p,tot_placed,tot_usn=getAvgMarks(year,ele['courseCode'],empid)
            tot_offers = Count(stud)
            if {'subname':ele['courseName'],'usnCount':tot_usn,'placeCount':tot_placed,'offerCount':tot_offers} not in placement:
                placement.append({'subname':ele['courseName'],'usnCount':tot_usn,'placeCount':tot_placed,'offerCount':tot_offers} )
            # if {'subname':ele['courseName'],'iaDetails':data,'usnCount':tot_usn,'placeCount':tot_placed,'offerCount':tot_offers} not in lst:
            #     lst.append({'subname':ele['courseName'],'iaDetails':data,'usnCount':tot_usn,'placeCount':tot_placed,'offerCount':tot_offers})
            # else:
            #     continue

            # lst.append({'subname':ele['courseName'],'iaDetails':data,'usnCount':tot_usn,'placeCount':tot_placed,'offerCount':tot_offers})
    # print(tot_usn,tot_placed,tot_offers)
    return lst,placement

getInternal('2017-18','6','ISE577')

# getSubjects('2017-18','6','ISE577')


# getAvgMarks('2017-18','15CS61','ISE577')



def get_avg_attendance(usn,courseCode,section,termNumber,deptId,year):

    for attedance_details in dhi_student_attendance.aggregate([
        {'$unwind': '$departments'},
        {'$unwind':'$students'},
        
    
        {
            '$match':
                    {
                    'academicYear':year,
                    'students.usn':usn,
                    'courseCode': courseCode,
                    'students.deptId': deptId,
                    'students.section':section,
                    'students.termNumber':termNumber
                    }
        },
      
        {
            '$project':
                    {
                        '_id':0,
                        'totalNumberOfClasses':'$students.totalNumberOfClasses',
                        'totalPresent':'$students.presentCount',
                        'totalAbsent':'$students.absentCount'
                    }
        }
 
    ]):
        attendance_per = (attedance_details['totalPresent']/attedance_details['totalNumberOfClasses'])*100
        attendance_per = round(attendance_per,2)
        attendance = {"attedance_details":attedance_details,"attendance_per":attendance_per}
        return attendance



def get_iadate_wise_attendance(usn,courseCode,section,termNumber,deptId,year,iadate,iaNumber):
    present_details = []
    present = []
    absent = []
    perc_of_present = 0
    perc_of_absent = 0 
    for x in dhi_student_attendance.aggregate([
        {'$unwind': '$departments'},
        {'$unwind':'$students'},
        {
            '$match':
                    {
                    'academicYear':year,
                    'students.usn':usn,
                    'courseCode': courseCode,
                    'students.deptId': deptId,
                    'students.section':section,
                    'students.termNumber':termNumber
                    }
        },
        {'$unwind':'$students.studentAttendance'},
        { 
            '$match': 
            {
                "students.studentAttendance.date":{"$lte":iadate}
            }   
        },      
        {
            '$project':
                    {
                        "_id":0,
                        "date":"$students.studentAttendance.date",
                        "present":"$students.studentAttendance.present"
                    }
        }
 
    ]):
        present_details.append(x['present'])
        if x['present'] == True:
            present.append(x['present'])
        if x['present'] == False:
            absent.append(x['present'])
    try:
        perc_of_present = (len(present)/len(present_details))*100
        perc_of_present = round(perc_of_present,2)
        perc_of_absent = (len(absent)/len(present_details))*100
        perc_of_absent = round(perc_of_absent,2)
    except:
        perc_of_present = 0 
        perc_of_absent = 0

    return perc_of_present,perc_of_absent


def get_details(usn,year,terms):   
    final_attendance = []

    for x in dhi_internal.aggregate([
        {'$unwind':'$studentScores'},
        {'$unwind':'$departments'},
        {
        '$match':
        {
            'studentScores.usn':usn,
            'academicYear': year,
            'departments.termNumber': {'$in':terms}
        }
        },
        {
            '$group':
            {
                '_id':
                {
                    'courseCode': '$courseCode',
                    'courseName': '$courseName',
                    'section': '$studentScores.section',
                    'termNumber': '$studentScores.termNumber',
                    'deptId': '$departments.deptId'
                }   
            }
        }
    ]):
        details = {}
        ia_details,avg_ia_score = get_ia_details(usn,x['_id']['courseCode'],x["_id"]
                                ["section"],x["_id"]["termNumber"], x["_id"]["deptId"],year)
        attedance_total_avg_details = get_avg_attendance(usn,x['_id']['courseCode'],x["_id"]
                                ["section"],x["_id"]["termNumber"], x["_id"]["deptId"],year)
        for ia_detail in ia_details:
            try:
                ia_detail['perc_of_present'],ia_detail['perc_of_absent'] = get_iadate_wise_attendance(usn,x['_id']['courseCode'],x["_id"]
                                    ["section"],x["_id"]["termNumber"], x["_id"]["deptId"],year,ia_detail['startTime'],ia_detail['iaNumber'])
            except KeyError:
                ia_detail['perc_of_present'] = 0 
                ia_detail['perc_of_absent'] = 0
        details['total_avg'] = {}
        details['attendance_per'] = 0
        details['courseCode'] = x['_id']['courseCode']
        details['courseName'] = x['_id']['courseName']
        details['section'] = x['_id']['section']
        details['termNumber'] = x['_id']['termNumber']
        details['deptId'] = x['_id']['deptId']
        details['ia_attendance_%'] = ia_details
        details['avg_ia_score'] = avg_ia_score
        if attedance_total_avg_details != None:
            details['total_avg'] = attedance_total_avg_details['attedance_details']
            details['attendance_per'] = attedance_total_avg_details['attendance_per']
        final_attendance.append(details)
    return final_attendance
# get_details('4MT16CV004','2017-18',['1','2','3','4','5','6','7','8'])