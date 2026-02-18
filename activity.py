from cltre import LTRE

eng = LTRE('inclass', debugging=False)

eng.assert_fact(("isa", "student", "student"))
eng.assert_fact(("isa", "CS101", "Course"))
eng.assert_fact(("isa", "CS102", "Course"))
eng.assert_fact(("isa", "CS103", "Course"))

eng.assert_fact(("requires", "CS102", "CS101"))
eng.assert_fact(("requires", "CS103", "CS102"))

eng.assert_fact(("offered", "CS102", "Fall"))
eng.assert_fact(("offered", "CS103", "Spring"))

eng.assert_fact(("availeSeats", "1", "CS102"))
eng.assert_fact(("teaches", "teacherA", "CS102"))
eng.assert_fact(("teaches", "teacherB", "CS103"))

#eng.uassume(("taken", "CS101", "student"), reason="pastCourse")
#eng.uassume(("needs", "CS102", "student"), reason="graduate")

eng.assert_fact(("taken", "CS101", "student"), just="assumed")
eng.assert_fact(("needs", "CS103", "student"), just="assumed")
eng.assert_fact(("enrolledIn", "CS102", "student"), just="assumed")


def eligible(env, trigger_node):
    prereq = env["?p"]
    student = env["?s"]

    courses = eng.fetch(("requires", "?c", prereq))
    
    for (_, course, _) in courses:
        offered = eng.fetch(("offered", course, "?sem"))
        if offered:
            eng.assert_fact(("eligible", student, course), just=("rule", "eligible"),
                dependencies=[("taken", prereq, student),("requires", course, prereq),offered[0]])

eng.add_rule(
    ("TRUE", ("taken", "?p", "?s")), eligible, name="eligible")


def finished(env, trigger_node):
    student = env["?s"]
    
    eng.assert_fact(("completedCourses", student), just=("rule", "finished"),
        dependencies=[("taken", "CS103", student)])

eng.add_rule(("TRUE", ("taken", "CS103", "?s")), finished, name="finished")

eng.run_rules()

print(eng.fetch(("taken", "?c", "student")))
print(eng.fetch(("eligible", "student", "?c")))
print(eng.fetch(("needs", "?c", "student")))
print(eng.fetch(("completedCourses", "student")))

eng.assert_fact(("taken", "CS102", "student"), just="assumed")
eng.assert_fact(("enrolledIn", "CS103", "student"), just="assumed")


eng.retract(("enrolledIn", "CS102", "student"), reason="passed")

eng.run_rules()

print(eng.fetch(("taken", "?c", "student")))
print(eng.fetch(("eligible", "student", "?c")))
print(eng.fetch(("needs", "?c", "student")))
print(eng.fetch(("completedCourses", "student")))

eng.assert_fact(("taken", "CS103", "student"), just="assumed")

eng.retract(("enrolledIn", "CS103", "student"), reason="passed")
eng.retract(("needs", "CS103", "student"), reason="passed")

eng.run_rules()

print(eng.fetch(("taken", "?c", "student")))
print(eng.fetch(("eligible", "student", "?c")))
print(eng.fetch(("needs", "?c", "student")))
print(eng.fetch(("completedCourses", "student")))
