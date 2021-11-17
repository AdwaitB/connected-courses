from flask import Flask, Response, request
from json import dumps
import time

from py2neo import Graph, Node, Relationship


app = Flask(__name__, static_url_path='/static/')

def read_csv():
    # read line by line records from a csv file courses.csv
    # return a list of records
    records = []
    with open('courses.csv', 'r') as f:
        for line in f:
            record = line.strip().split(',')
            if record[5] != 'A' or record[7] == 'TBA' or record[1] == 'Special Problems':
                continue
            records.append(record)
            print(record[1])
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

def post_to_neo4j(records):
    # connect to the graph
    graph = Graph("http://localhost:7474")
    print("Deleting pre-existing records... ")
    graph.delete_all()
    # create nodes
    nodes = []
    relationships = []
    for record in records:
        # create a node for each record
        course = Node("Course", name=record[1], CRM=record[2],
                      department=record[3], coursecode=record[4],
                      section=record[5], credits=record[6],
                      time=record[7], days=record[8],
                      location=record[9], instructor=record[10])
        nodes.append(course)

    for i in range(len(records)):
        # create relationships
        for j in range(len(records)):
            if i == j:
                continue
            if records[i][7] != records[j][7]:
                relationship = Relationship(nodes[i], "CAN_BE_TAKEN_WTIH", nodes[j])
                relationships.append(relationship)

    print(len(relationships))

    tx = graph.begin()
    for node in nodes:
        tx.create(node)
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

