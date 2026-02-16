from cltre import LTRE

eng = LTRE('inclass', debugging=False)

eng.assert_fact(("isa", "ryan", "student"))
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

#eng.uassume(("taken", "CS101", "ryan"), reason="pastCourse")
#eng.uassume(("needs", "CS102", "ryan"), reason="graduate")

eng.assert_fact(("taken", "CS101", "ryan"), just="assumed")
eng.assert_fact(("needs", "CS103", "ryan"), just="assumed")
eng.assert_fact(("enrolledIn", "CS102", "ryan"), just="assumed")


