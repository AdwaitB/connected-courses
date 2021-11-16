from typing import List, Dict, Any

import pandas as pd
from bs4 import BeautifulSoup

# 1 is HTML, 2 is STRING
CREDIT_PARSER_MODE = 2


def readFile(filepath):
    with open(filepath, 'r') as file:
        return file.read()


def doNext(splits, count):
    ret = splits
    for i in range(count):
        ret = ret.next
    return ret


class Course:
    courseNameEntry = ""
    name = ""
    crn = 0
    department = ""
    code = ""
    section = ""

    credits = ""
    time = ""
    days = ""
    location = ""
    instructor = ""

    def to_dict(self):
        return{
            "Course Name": self.name,
            "CRM": self.crn,
            "Department": self.department,
            "Course Code": self.code,
            "Section": self.section,
            "Credits": self.credits,
            "Time": self.time,
            "Days": self.days,
            "Location": self.location,
            "Instructor": self.instructor
        }

    def parse(self):
        pass

    def setCredits(self, credits, prevCred):
        try:
            self.credits = int(float(credits.replace("Credits", "").replace(" ", "")))
        except ValueError:
            self.credits = "VAR"
        if self.credits == 0:
            self.credits = prevCred

    def setCourseName(self, courseName):
        self.courseNameEntry = courseName
        splits = courseName.split(" - ")
        self.name = splits[0]
        self.crn = int(splits[1])
        self.department = splits[2].split(" ")[0]
        self.code = splits[2].split(" ")[1]
        self.section = splits[3]

    def validate(self):
        return True


def readHTML(filename):
    return BeautifulSoup(readFile(filename), features="html.parser")


def parse(html):
    coursesTable = html.find("div", "pagebodydiv").find("table", "datadisplaytable").find_all('tr')

    courses = []

    prevCred = -1

    for i in range(0, len(coursesTable), 4):
        course = Course()
        try:
            course.setCourseName(coursesTable[i].find("th").find("a").text)
        except:
            continue
    
        if CREDIT_PARSER_MODE == 1:
            brSplits = coursesTable[i + 1].find("br")
            course.setCredits(entry, prevCred)
        elif CREDIT_PARSER_MODE == 2:
            nlSplits = coursesTable[i + 1].text.split("\n\n")
            for entry in nlSplits:
                if entry.find("Credits") != -1:
                    course.setCredits(entry, prevCred)
                    prevCred = course.credits
                    break
    
        tableEntries = coursesTable[i + 3].find_all("td")

        if len(tableEntries) < 7:
            continue

        course.time = tableEntries[1].text
        course.days = tableEntries[2].text
        course.location = tableEntries[3].text
        course.instructor = tableEntries[6].text

        if course.validate():
            courses.append(course.to_dict())

    return courses


html = BeautifulSoup(readFile("CS_complete.html"), features="html.parser")
courses = parse(html)
courses = pd.DataFrame.from_records(courses)
courses.to_csv("courses.csv")
