import pandas as pd
from html.parser import HTMLParser
from bs4 import BeautifulSoup


def readFile(filepath):
    with open(filepath, 'r') as file:
        return file.read()


def doNext(splits, count):
    ret = splits
    for i in range(count):
        ret = ret.next
    return ret


class Course:
    courseName = ""
    credits = ""
    time = ""
    days = ""
    location = ""
    instructor = ""

    def to_dict(self):
        return{
            "Course Name": self.courseName,
            "Credits": self.credits,
            "Time": self.time,
            "Days": self.days,
            "Location": self.location,
            "Instructor": self.instructor
        }


    def validate(self):
        return True


rawData = readFile("Class Schedule Listing.html")
parsedData = BeautifulSoup(rawData, features="html.parser")
parsedData.find("div", "pagebodydiv").find("table", "datadisplaytable")
coursesTable = parsedData.find("div", "pagebodydiv").find("table", "datadisplaytable").find_all('tr')

courses = []

for i in range(0, len(coursesTable), 4):
    course = Course()
    course.courseName = coursesTable[i].find("th").find("a").text

    brSplits = coursesTable[i+1].find("br")
    course.credits = doNext(brSplits, 27)

    tableEntries = coursesTable[i+3].find_all("td")
    course.time = tableEntries[1].text
    course.days = tableEntries[2].text
    course.location = tableEntries[3].text
    course.instructor = tableEntries[6].text

    if course.validate():
        courses.append(course.to_dict())

courses = pd.DataFrame.from_records(courses)
courses.to_csv("courses.csv")
