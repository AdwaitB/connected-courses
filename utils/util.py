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
    positive_filters = []
    negative_filters = []
    def __init__(self, number_of_courses, positive_filters, negative_filters):
        self.number_of_courses = number_of_courses
        self.positive_filters = positive_filters
        self.negative_filters = negative_filters
    
    def generate_query(self):
        query = "MATCH "

        for i in range(self.number_of_courses):
            for j in range(i+1, self.number_of_courses):
                query += "(c" + str(i+1) + ")-[:CAN_BE_TAKEN_WITH]-(c" + str(j+1) + ")," 

        query = query[:-1] 
        
        query += " WHERE "

        for i in range(len(self.positive_filters)):
            if self.positive_filters[i].course_name != '':
                query += "c" + str(i+1) + ".name = '" + self.positive_filters[i].course_name + "' AND "
            if len(self.positive_filters[i].instructors) > 0:
                query += "("
                for k in range(len(self.positive_filters[i].instructors)):
                    query += "(c" + str(i+1) + ")-[:TEACHES]-(:Instructor {name:'" + self.positive_filters[i].instructors[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "
            if len(self.positive_filters[i].fields) > 0:
                query += "("
                for k in range(len(self.positive_filters[i].fields)):
                    query += "(c" + str(i+1) + ")-[:IS_RELATED_TO]-(:Field {name:'" + self.positive_filters[i].fields[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "
            if len(self.positive_filters[i].days) > 0:
                query += "("
                for k in range(len(self.positive_filters[i].days)):
                    query += "(c" + str(i+1) + ")-[:TAUGHT_ON]-(:Day {name:'" + self.positive_filters[i].days[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "
            if len(self.positive_filters[i].locations) > 0:
                query += "("
                for k in range(len(self.positive_filters[i].locations)):
                    query += "(c" + str(i+1) + ")-[:TAUGHT_AT]-(:Location {name:'" + self.positive_filters[i].locations[k] + "'})" + " OR "
                query = query[:-4]
                query += ") AND "

        for i in range(len(self.negative_filters)):
            if self.negative_filters[i].course_name != '':
                query += "c" + str(i+1) + ".name <> '" + self.negative_filters[i].course_name + "' AND "
            if len(self.negative_filters[i].instructors) > 0:
                query += "("
                for k in range(len(self.negative_filters[i].instructors)):
                    query += "NOT (c" + str(i+1) + ")-[:TEACHES]-(:Instructor {name:'" + self.negative_filters[i].instructors[k] + "'})" + " AND "
                query = query[:-5]
                query += ") AND "
            if len(self.negative_filters[i].fields) > 0:
                query += "("
                for k in range(len(self.negative_filters[i].fields)):
                    query += "NOT (c" + str(i+1) + ")-[:IS_RELATED_TO]-(:Field {name:'" + self.negative_filters[i].fields[k] + "'})" + " AND "
                query = query[:-5]
                query += ") AND "
            if len(self.negative_filters[i].days) > 0:
                query += "("
                for k in range(len(self.negative_filters[i].days)):
                    query += "NOT (c" + str(i+1) + ")-[:TAUGHT_ON]-(:Day {name:'" + self.negative_filters[i].days[k] + "'})" + " AND "
                query = query[:-5]
                query += ") AND "
            if len(self.negative_filters[i].locations) > 0:
                query += "("
                for k in range(len(self.negative_filters[i].locations)):
                    query += "NOT (c" + str(i+1) + ")-[:TAUGHT_AT]-(:Location {name:'" + self.negative_filters[i].locations[k] + "'})" + " AND "
                query = query[:-5]
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
    positive_courses = []
    positive_instructors = []
    positive_fields = []
    positive_days = []
    positive_locations = []
    positive_course_to_fields = {}

    negative_courses = []
    negative_instructors = []
    negative_fields = []
    negative_days = []
    negative_locations = []
    negative_course_to_fields = {}

    def __init__(self, positive_courses, negative_courses, positive_instructors, negative_instructors, positive_fields, negative_fields, positive_days, negative_days, positive_locations, negative_locations, course_to_fields):
        self.positive_courses = positive_courses
        self.positive_instructors = positive_instructors
        self.positive_fields = positive_fields
        self.positive_days = positive_days
        self.positive_locations = positive_locations

        self.negative_courses = negative_courses
        self.negative_instructors = negative_instructors
        self.negative_fields = negative_fields
        self.negative_days = negative_days
        self.negative_locations = negative_locations

        self.course_to_fields = course_to_fields
    
    def evaluate(self, result):
        score = 0
        matched_preferences = []
        for course in result.info:
            if result.info[course]['name'] in self.positive_courses:
                score += 1
                matched_preferences.append('POSITIVE: Course Name' + ': ' + result.info[course]['name'] + "(" + result.info[course]['name'] + ")")
            if result.info[course]['name'] in self.negative_courses:
                score -= 1
                matched_preferences.append('NEGATIVE: Course Name' + ': ' + result.info[course]['name'] + "(" + result.info[course]['name'] + ")")

            if result.info[course]['instructor'] in self.positive_instructors:
                score += 1
                matched_preferences.append('POSITIVE: Instructor' + ': ' + result.info[course]['instructor'] + "(" + result.info[course]['name'] + ")")
            if result.info[course]['instructor'] in self.negative_instructors:
                score -= 1
                matched_preferences.append('NEGATIVE: Instructor' + ': ' + result.info[course]['instructor'] + "(" + result.info[course]['name'] + ")")

            for field in self.course_to_fields[result.info[course]['name']]:
                if field in self.positive_fields:
                    score += 1
                    matched_preferences.append('POSITIVE: Field' + ': ' + field + "(" + result.info[course]['name'] + ")")
                    break
            for field in self.course_to_fields[result.info[course]['name']]:
                if field in self.negative_fields:
                    score -= 1
                    matched_preferences.append('NEGATIVE: Field' + ': ' + field + "(" + result.info[course]['name'] + ")")
                    break

            for day in result.info[course]['days']:
                if day in self.positive_days:
                    score += 1
                    matched_preferences.append('POSITIVE: Day' + ': ' + day + "(" + result.info[course]['name'] + ")")
                    break
            for day in result.info[course]['days']:
                if day in self.negative_days:
                    score -= 1
                    matched_preferences.append('NEGATIVE: Day' + ': ' + day + "(" + result.info[course]['name'] + ")")
                    break


            if result.info[course]['location'] in self.positive_locations:
                score += 1
                matched_preferences.append('POSITIVE: Location' + ': ' + result.info[course]['location'] + "(" + result.info[course]['name'] + ")")
            if result.info[course]['location'] in self.negative_locations:
                score -= 1
                matched_preferences.append('NEGATIVE: Location' + ': ' + result.info[course]['location'] + "(" + result.info[course]['name'] + ")")

        result.score = score
        result.matched_preferences = matched_preferences

        return result

    def __str__(self):
        return "Positive Courses: " + str(self.positive_courses) + "\n" + "Negative Courses: " + str(self.negative_courses) + "\n" + "Positive Instructors: " + str(self.positive_instructors) + "\n" + "Negative Instructors: " + str(self.negative_instructors) + "\n" + "Positive Fields: " + str(self.positive_fields) + "\n" + "Negative Fields: " + str(self.negative_fields) + "\n" + "Positive Days: " + str(self.positive_days) + "\n" + "Negative Days: " + str(self.negative_days) + "\n" + "Positive Locations: " + str(self.positive_locations) + "\n" + "Negative Locations: " + str(self.negative_locations) + "\n"



# if __name__ == "__main__":
    
#     # filter1 = Filter('', [] , [], [], [])
#     # filter2 = Filter('', [] , [], [], [])
#     # filter3 = Filter('', [] , [], [], [])
#     # filter4 = Filter('', [] , [], [], [])

#     filter1 = Filter('Adv Operating Systems', [], [], [], [])
#     filter2 = Filter('', ['Gerandy   Brito (P)'], [], [], [])
#     filter3 = Filter('', [], [], [], [])
#     filter4 = Filter('', [], [], ['M', 'W'], ['Scheller College of Business'])
#     positive_filters = [filter1, filter2, filter3, filter4]

#     negfilter1 = Filter('', [], [], [], [])
#     negfilter2 = Filter('', [], [], [], [])
#     negfilter3 = Filter('', [], [], [], [])
#     negfilter4 = Filter('', [], [], ['T', 'R'], ['College of Computing'])
#     negative_filters = [negfilter1, negfilter2, negfilter3, negfilter4]

#     query_generator = QueryGenerator(4, positive_filters, negative_filters)

#     print(query_generator.generate_query())