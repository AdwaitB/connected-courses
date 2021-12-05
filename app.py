from flask import Flask, Response, request
import json
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

# Sample Search results Page
@app.route("/results")
def show_results():
    return app.send_static_file('result.html')

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

# Function to handle a get request at /filter endpoint which accepts a JSON object
# containing the filters to be applied to the search
@app.route("/filter", methods=['GET'])
def filter():
    # Get the filters from the request
    filters = request.args.get('filters_list')
    filters = json.loads(filters)

    n_courses = len(filters)
    print("Number of courses:" + str(n_courses))

    # Get the preferences from the request
    preferences = request.args.get('preferences_list')
    preferences = json.loads(preferences)
    
    positive_filter_list = []
    negative_filter_list = []

    for filter in filters:
        course_filter = filter['positive_courses_filters'][0] if len(filter['positive_courses_filters']) > 0 else ""
        instructor_list = filter['positive_instructors_filters']
        field_list = filter['positive_fields_filters']
        location_list = filter['positive_locations_filters']
        day_list = filter['positive_days_filters']
        positive_filter_list.append(Filter(course_filter, instructor_list, field_list, location_list, day_list))

        negative_course_filter = filter['negative_courses_filters'][0] if len(filter['negative_courses_filters']) > 0 else ""
        negative_instructor_list = filter['negative_instructors_filters']
        negative_field_list = filter['negative_fields_filters']
        negative_location_list = filter['negative_locations_filters']
        negative_day_list = filter['negative_days_filters']
        negative_filter_list.append(Filter(negative_course_filter, negative_instructor_list, negative_field_list, negative_location_list, negative_day_list))

    # Create a QueryGenerator object
    query_generator = QueryGenerator(len(positive_filter_list), positive_filter_list, negative_filter_list)

    preferences_object = Preferences(preferences['positive_courses_preferences'], preferences['negative_courses_preferences'], \
    preferences['positive_instructors_preferences'], preferences['negative_instructors_preferences'], \
    preferences['positive_fields_preferences'], preferences['negative_fields_preferences'], \
    preferences['positive_locations_preferences'], preferences['negative_locations_preferences'], \
    preferences['positive_days_preferences'], preferences['negative_days_preferences'], \
    course_to_fields)

    graph = Graph("http://localhost:7474")
    result_set = graph.run(query_generator.generate_query()).data()

    result_objects = []
    for result in result_set:
        result_object = Result(result)
        result_objects.append(result_object)
    
    for i in range(len(result_objects)):
        result_objects[i] = preferences_object.evaluate(result_objects[i])

    result_objects.sort(key=lambda x: x.score, reverse=True)

    print("Ordered Suggestions")

    nodes = []
    links = []
    scores = []
    data = {}
    count = 1
    prev = 0

    yiteration = 0
    for result in result_objects:
        # print("________________________________________________________")
        # for course in result.info:
        #     print(result.info[course]['name'] + " " + str(result.info[course]['time']))
        # print("Score " + str(result.score))
        # result.matched_preferences.sort()
        # print("Matched preferences " + str(result.matched_preferences))

        xiteration = 0
        for course in result.info:
            course_name = result.info[course]['name']
            matched_preferences = []
            for preference in result.matched_preferences:
                if course_name in preference:
                    matched_preferences.append(preference)
            matched_preferences.sort()
            # Create a string from matched_preferences
            matched_preferences_string = ""
            for preference in matched_preferences:
                matched_preferences_string += preference + " "
            if xiteration % n_courses == 0:
                nodes.append({"matchedpreferences":matched_preferences_string, "x": 50 + xiteration * 300 , "y": 50 + yiteration * 100, "id":"Score:" + str(result.score) + " " + str(count) + " " + result.info[course]['name'], "name": result.info[course]['name'], "professor": result.info[course]['instructor'], "field": result.info[course]['field'], "location": result.info[course]['location'], "days": result.info[course]['day'], "score": result.score})
            else:
                nodes.append({"matchedpreferences":matched_preferences_string, "x": 50 + xiteration * 300 , "y": 50 + yiteration * 100, "id":str(count) + " " + result.info[course]['name'], "name": result.info[course]['name'], "professor": result.info[course]['instructor'], "field": result.info[course]['field'], "location": result.info[course]['location'], "days": result.info[course]['day'], "score": result.score})
            xiteration += 1

        for i in range(prev, len(nodes) - 1):
            links.append({"source": nodes[i]['id'], "target": nodes[i+1]['id'], "value": 10})

        prev = len(nodes)
        count += 1
        yiteration += 1

    data['nodes'] = nodes
    data['links'] = links

    return Response(dumps(data),
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

