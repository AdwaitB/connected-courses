from flask import Flask, Response, request
from json import dumps
import time

from py2neo import Graph, Node, Relationship

from utils.util import Filter, QueryGenerator, Preferences, Result

app = Flask(__name__, static_url_path='/static/')

course_to_fields = {}

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

# Sample Search results Page
@app.route("/results")
def show_results():
    return app.send_static_file('result.html')

# Write a handler for a get request on /search
@app.route("/search/<coursename>")
def search(coursename):
    graph = Graph("http://localhost:7474")
    coursenode = graph.nodes.match("Course", name=coursename).first()

    filter1 = Filter('Machine Learning', [], [], [], [])
    filter2 = Filter('', [], [], [], [])
    filter3 = Filter('', [], ['Other', 'HCI'], [], [])
    filter4 = Filter('', [], [], [], ['Scheller College of Business'])
    positive_filters = [filter1, filter2, filter3, filter4]

    negfilter1 = Filter('', [], [], [], [])
    negfilter2 = Filter('', [], [], [], [])
    negfilter3 = Filter('', [], [], [], [])
    negfilter4 = Filter('', [], [], [], ['R,J. Erskine Love Manufacturing'])
    negative_filters = [negfilter1, negfilter2, negfilter3, negfilter4]

    query_generator = QueryGenerator(4, positive_filters, negative_filters)
    result_set = graph.run(query_generator.generate_query()).data()

    preferences = Preferences([], [], \
    ['Umakishore   Ramachandran (P)', 'Gerandy   Brito (P)'], ['Ada   Gavrilovska (P)'], \
    ['Security', 'Networks', 'HCI'], ['Computer Vision', 'Machine Learning'], \
    ['T'], ['R', 'F'], \
    ['Scheller College of Business', 'Klaus Advanced Computing', 'College of Computing', 'Instructional Center'], ['R,J. Erskine Love Manufacturing'], \
    course_to_fields)

    print("Positive Filters are:")
    for filter in positive_filters:
        print(filter)
    print("Negative Filters are:")
    for filter in negative_filters:
        print(filter)

    print("Preferences are :")
    print(preferences)
    result_objects = []
    for result in result_set:
        result_object = Result(result)
        result_objects.append(result_object)
    
    for i in range(len(result_objects)):
        result_objects[i] = preferences.evaluate(result_objects[i])

    result_objects.sort(key=lambda x: x.score, reverse=True)

    print("Ordered Suggestions")

    for result in result_objects:
        print("________________________________________________________")
        for course in result.info:
            print(result.info[course]['name'] + " " + str(result.info[course]['time']))
        print("Score " + str(result.score))
        result.matched_preferences.sort()
        print("Matched preferences " + str(result.matched_preferences))
        

    return Response(dumps(serialize_course(coursenode)),
                    mimetype="application/json")

# Write a function to service a get request to the /populate endpoint
@app.route("/populate")
def populate():
    reply = {}

    # Query the db for a list of names of all Instructors
    graph = Graph("http://localhost:7474")
    instructors = graph.nodes.match("Instructor").all()
    reply['instructors'] = []
    for instructor in instructors:
        reply['instructors'].append(instructor['name'])
        # Sort reply['instructors'] alphabetically
    reply['instructors'].sort()

    # Query the db for a list of names of all Fields
    fields = graph.nodes.match("Field").all()
    reply['fields'] = []
    for field in fields:
        reply['fields'].append(field['name'])
        # Sort reply['fields'] alphabetically
    reply['fields'].sort()

    # Query the db for a list of names of all Courses
    courses = graph.nodes.match("Course").all()
    reply['courses'] = []
    for course in courses:
        reply['courses'].append(course['name'])
        # Sort reply['courses'] alphabetically
    reply['courses'].sort()

    # Query the db for a list of names of all Locations
    locations = graph.nodes.match("Location").all()
    reply['locations'] = []
    for location in locations:
        reply['locations'].append(location['name'])
        # Sort reply['locations'] alphabetically
    reply['locations'].sort()

    # Query the db for a list of names of all Days
    days = graph.nodes.match("Day").all()
    reply['days'] = []
    for day in days:
        reply['days'].append(day['name'])
        # Sort reply['days'] alphabetically
    reply['days'].sort()
    

    return Response(dumps(reply),
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
    global course_to_fields
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
                                       department=record[3], coursecode=int(record[4]),
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

