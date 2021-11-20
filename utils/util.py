class Filter:
    course_name = ''
    instructors = []
    fields = []
    days = []
    locations = []

    def __init__(self, course_name, instructors, fields, days, locations):
        self.course_name = course_name
        self.instructors = instructors
        self.fields = fields
        self.days = days
        self.locations = locations

    def __str__(self):
        return "Course: " + self.course_name + "\tInstructors: " + str(self.instructors) + "\tFields: " + str(self.fields) + "\tDays: " + str(self.days) + "\tLocations: " + str(self.locations)

class QueryGenerator:
    number_of_courses = 0
    filters = []
    def __init__(self, number_of_courses, filters):
        self.number_of_courses = number_of_courses
        self.filters = filters
    
    def generate_query(self):
        query = "MATCH "

        for i in range(self.number_of_courses):
            for j in range(i+1, self.number_of_courses):
                query += "(c" + str(i+1) + ")-[:CAN_BE_TAKEN_WITH]-(c" + str(j+1) + ")," 

        query = query[:-1] 
        
        query += " WHERE "

        for i in range(len(self.filters)):
            if self.filters[i].course_name != '':
                query += "c" + str(i+1) + ".name = '" + self.filters[i].course_name + "' AND "
            if len(self.filters[i].instructors) > 0:
                query += "("
                for k in range(len(self.filters[i].instructors)):
                    query += "(c" + str(i+1) + ")-[:TEACHES]-(:Instructor {name:'" + self.filters[i].instructors[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "
            if len(self.filters[i].fields) > 0:
                query += "("
                for k in range(len(self.filters[i].fields)):
                    query += "(c" + str(i+1) + ")-[:IS_RELATED_TO]-(:Field {name:'" + self.filters[i].fields[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "
            if len(self.filters[i].days) > 0:
                query += "("
                for k in range(len(self.filters[i].days)):
                    query += "(c" + str(i+1) + ")-[:TAUGHT_ON]-(:Day {name:'" + self.filters[i].days[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "
            if len(self.filters[i].locations) > 0:
                query += "("
                for k in range(len(self.filters[i].locations)):
                    query += "(c" + str(i+1) + ")-[:TAUGHT_AT]-(:Location {name:'" + self.filters[i].locations[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "
            
            
        if query[-7:] == " WHERE ":
            query = query[:-7]
        else:
            query = query[:-5]

        query += " RETURN "
        for i in range(self.number_of_courses):
            query += "c" + str(i+1) + ", "
        query = query[:-2]

        return query

class Result:
    info = {}
    score = 0
    matched_preferences = []

    def __init__(self, info = None, score = None, matched_preferences = None):
        if info is not None:
            self.info = info
        if score is not None:
            self.score = score
        if matched_preferences is not None:
            self.matched_preferences = matched_preferences

class Preferences:
    courses = []
    instructors = []
    fields = []
    days = []
    locations = []
    course_to_fields = {}

    def __init__(self, courses, instructors, fields, days, locations, course_to_fields):
        self.courses = courses
        self.instructors = instructors
        self.fields = fields
        self.days = days
        self.locations = locations
        self.course_to_fields = course_to_fields
    
    def evaluate(self, result):
        score = 0
        matched_preferences = []
        for course in result.info:
            if result.info[course]['name'] in self.courses:
                score += 1
                matched_preferences.append('Course Name' + ': ' + result.info[course]['name'] + "(" + result.info[course]['name'] + ")")

            if result.info[course]['instructor'] in self.instructors:
                score += 1
                matched_preferences.append('Instructor' + ': ' + result.info[course]['instructor'] + "(" + result.info[course]['name'] + ")")

            for field in self.course_to_fields[result.info[course]['name']]:
                if field in self.fields:
                    score += 1
                    matched_preferences.append('Field' + ': ' + field + "(" + result.info[course]['name'] + ")")
                    break

            for day in result.info[course]['days']:
                if day in self.days:
                    score += 1
                    matched_preferences.append('Day' + ': ' + day + "(" + result.info[course]['name'] + ")")
                    break


            if result.info[course]['location'] in self.locations:
                score += 1
                matched_preferences.append('Location' + ': ' + result.info[course]['location'] + "(" + result.info[course]['name'] + ")")

        result.score = score
        result.matched_preferences = matched_preferences

        return result

    def __str__(self):
        return "Courses: " + str(self.courses) + "\nInstructors: " + str(self.instructors) + "\nFields: " + str(self.fields) + "\nDays: " + str(self.days) + "\nLocations: " + str(self.locations)



# if __name__ == "__main__":
    
#     # filter1 = Filter('', [] , [], [], [])
#     # filter2 = Filter('', [] , [], [], [])
#     # filter3 = Filter('', [] , [], [], [])
#     # filter4 = Filter('', [] , [], [], [])

#     filter1 = Filter('Adv Operating Systems', [], [], [], [])
#     filter2 = Filter('', ['Gerandy   Brito (P)'], [], [], [])
#     filter3 = Filter('', [], [], [], [])
#     filter4 = Filter('', [], [], ['M', 'W'], ['Scheller College of Business'])
#     filters = [filter1, filter2, filter4, filter3]

#     query_generator = QueryGenerator(4, filters)

#     print(query_generator.generate_query())