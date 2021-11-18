from flask import Flask, Response, request
from json import dumps
import time

from py2neo import Graph, Node, Relationship

app = Flask(__name__, static_url_path='/static/')

def convert_to_24_format(time):
    # 12:30 PM -> 1230

    isPM = 'pm' in time

    a = time.split(':')[0] # 12
    b = time.split(':')[1][:2] # 30

    if isPM:
        if a == '12':
            return int(a + b)
        else:
            return int(str(int(a) + 12) + b)
    else:
        if a == '12':
            return int('00' + b)
        else:
            return int(a + b)




def overlap(time1, time2):
    # Check if two time ranges overlap
    start1 = convert_to_24_format(time1.split('-')[0])
    end1 = convert_to_24_format(time1.split('-')[1])
    start2 = convert_to_24_format(time2.split('-')[0])
    end2 = convert_to_24_format(time2.split('-')[1])

    if start1 <= end2 and end1 >= start2:
        return True
    else:
        return False

def read_csv():
    # read line by line records from a csv file courses.csv
    # return a list of records
    records = []
    with open('courses.csv', 'r') as f:
        for line in f:
            record = line.strip().split(',')
            if (record[5] != 'A' and record[5] != 'B') or record[7] == 'TBA' or record[1] == 'Special Problems':
                continue
            # Remove last word in location string
            record[9] = record[9]
            record[9] = record[9].rsplit(' ', 1)[0]
            records.append(record)
    return records

def serialize_course(course):
    return {
        'Course': course['name'],
        'CRM': course['CRM'],
        'department': course['department'],
        'coursecode': course['coursecode'],
        'section': course['section'],
        'credits': course['credits'],
        'time': course['time'],
        'days': course['days'],
        'location': course['location'],
        'instructor': course['instructor']
    }

@app.route("/")
def hello_world():
    return app.send_static_file('landing.html')

# Write a handler for a get request on /search
@app.route("/search/<coursename>")
def search(coursename):
    graph = Graph("http://localhost:7474")
    coursenode = graph.nodes.match("Course", name=coursename).first()
    print(coursenode)
    return Response(dumps(serialize_course(coursenode)),
                    mimetype="application/json")

# Write a function to read tags from a file where the line is of the form field: tag1, tag2, tag3
# Return a list of fields and tags
def read_tags(filename):
    fields = []
    course_to_fields = {}
    lineNumber = 0
    with open(filename, 'r') as f:
        for line in f:
            if lineNumber == 0:
                for field in line.strip().split(','):
                    fields.append(field)
                lineNumber += 1
                continue
            course = line.strip().split(':')[0]
            related_fields = line.strip().split(':')[1].split(',')
            course_to_fields[course] = related_fields
    print(fields)
    print(course_to_fields)
    return fields, course_to_fields

def post_to_neo4j(records):
    # connect to the graph
    graph = Graph("http://localhost:7474")
    print("Deleting pre-existing records... ")
    graph.delete_all()
    # create nodes
    courseNodes = []
    instructorNodes = []
    relationships = []
    instructors = {}
    courses = {}
    locations = {}
    locationNodes = []
    days = {}
    dayNodes = []
    fields = {}
    fieldNodes = []

    _, course_to_fields = read_tags('tags.txt')

    for record in records:
        coursename = record[1]
        if coursename not in courses:
            courses[coursename] = Node("Course", name=record[1], CRM=record[2],
                                       department=record[3], coursecode=record[4],
                                       section=record[5], credits=record[6],
                                       time=record[7], days=record[8],
                                       location=record[9], instructor=record[10])
            courseNodes.append(courses[coursename])
        else:
            continue
        if courses[coursename]['instructor'] not in instructors:
            instructors[courses[coursename]['instructor']] = Node("Instructor", name=courses[coursename]['instructor'])
            instructorNodes.append(instructors[courses[coursename]['instructor']])
        if courses[coursename]['location'] not in locations:
            locations[courses[coursename]['location']] = Node("Location", name=courses[coursename]['location'])
            locationNodes.append(locations[courses[coursename]['location']])
        for dayofweek in courses[coursename]['days']:
            if dayofweek not in days:
                days[dayofweek] = Node("Day", name=dayofweek)
                dayNodes.append(days[dayofweek])
        for field in course_to_fields[coursename]:
            if len(field) == 0:
                continue
            if field not in fields:
                fields[field] = Node("Field", name=field)
                fieldNodes.append(fields[field])
        
        print(courses[coursename]['name'])
    
    for i in range(len(courseNodes)):
        for j in range(i+1, len(courseNodes)):
            if i == j:
                continue
            if not overlap(courseNodes[i]['time'], courseNodes[j]['time']):
                relationships.append(Relationship(courseNodes[i], "CAN_BE_TAKEN_WITH", courseNodes[j]))
    
    for coursename, courseNode in courses.items():
        relationships.append(Relationship(instructors[courseNode['instructor']], "TEACHES", courses[coursename]))
        relationships.append(Relationship(courses[coursename], "TAUGHT_AT", locations[courseNode['location']]))
        for dayofweek in courseNode['days']:
            relationships.append(Relationship(courses[coursename], "TAUGHT_ON", days[dayofweek]))
        for field in course_to_fields[coursename]:
            if len(field) == 0:
                continue
            relationships.append(Relationship(courses[coursename], "IS_RELATED_TO", fields[field]))
    

    tx = graph.begin()
    for coursenode in courseNodes:
        tx.create(coursenode)
    for instructor in instructorNodes:
        tx.create(instructor)
    for location in locationNodes:
        tx.create(location)
    for field in fieldNodes:
        tx.create(field)
    for day in dayNodes:
        tx.create(day)

    for relationship in relationships:
        tx.create(relationship)
    graph.commit(tx)

def main():
    print("Reading from csv file...")
    records = read_csv()
    print("Len of records is " + str(len(records)))
    print("Posting to neo4j...")
    post_to_neo4j(records[1:])
    print("Posted to neo4j")
    print("Starting server...")
    app.run(host="localhost", port=5005, debug=True)

if __name__ == "__main__":
    main()

