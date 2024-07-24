import sqlite3
from prettytable import PrettyTable

# Set up the database connection and cursor
conn = sqlite3.connect('gradebook.db')
cursor = conn.cursor()

# Create tables if they do not exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    email TEXT PRIMARY KEY,
    names TEXT,
    GPA REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    name TEXT PRIMARY KEY,
    trimester TEXT,
    credits INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS registrations (
    student_email TEXT,
    course_name TEXT,
    grade REAL,
    FOREIGN KEY(student_email) REFERENCES students(email),
    FOREIGN KEY(course_name) REFERENCES courses(name)
)
''')

conn.commit()

class Student:
    def __init__(self, email, names):
        self.email = email
        self.names = names
        self.courses_registered = []
        self.GPA = 0.0

    def calculate_GPA(self):
        """Calculate the GPA based on registered courses and grades."""
        total_points = 0
        total_credits = 0
        for course, grade in self.courses_registered:
            total_points += grade * course.credits
            total_credits += course.credits
        self.GPA = total_points / total_credits if total_credits > 0 else 0
        # Update GPA in the database
        cursor.execute('UPDATE students SET GPA = ? WHERE email = ?', (self.GPA, self.email))
        conn.commit()

    def register_for_course(self, course, grade):
        """Register a course with a grade for the student."""
        self.courses_registered.append((course, grade))
        # Insert registration into the database
        cursor.execute('INSERT INTO registrations (student_email, course_name, grade) VALUES (?, ?, ?)', 
                       (self.email, course.name, grade))
        conn.commit()
        self.calculate_GPA()  # Recalculate GPA after registering for a course

class Course:
    def __init__(self, name, trimester, credits):
        self.name = name
        self.trimester = trimester
        self.credits = credits

class GradeBook:
    def __init__(self):
        self.student_list = []
        self.course_list = []

    def add_student(self):
        """Add a new student to the grade book."""
        email = input("Enter student's email: ")
        names = input("Enter student's names: ")
        new_student = Student(email, names)
        self.student_list.append(new_student)
        # Insert student into the database
        cursor.execute('INSERT INTO students (email, names, GPA) VALUES (?, ?, ?)', (email, names, 0.0))
        conn.commit()
        print("Student added successfully.")

    def add_course(self):
        """Add a new course to the grade book."""
        name = input("Enter course name: ")
        trimester = input("Enter trimester: ")
        credits = int(input("Enter course credits: "))
        new_course = Course(name, trimester, credits)
        self.course_list.append(new_course)
        # Insert course into the database
        cursor.execute('INSERT INTO courses (name, trimester, credits) VALUES (?, ?, ?)', (name, trimester, credits))
        conn.commit()
        print("Course added successfully.")

    def register_student_for_course(self):
        """Register a student for a course with a grade."""
        student_email = input("Enter student's email: ")
        course_name = input("Enter course name: ")
        grade = float(input("Enter grade: "))

        # Find the student and course
        student = next((s for s in self.student_list if s.email == student_email), None)
        course = next((c for c in self.course_list if c.name == course_name), None)

        if student and course:
            student.register_for_course(course, grade)
            print(f"Registered {student.names} for {course.name} with grade {grade}.")
        else:
            print("Student or course not found.")

    def calculate_ranking(self):
        """Sort the students by GPA in descending order and display the ranking."""
        self.student_list.sort(key=lambda s: s.GPA, reverse=True)
        print("Ranking of students by GPA:")
        for student in self.student_list:
            print(f"{student.names}: GPA = {student.GPA}")

    def search_by_grade(self):
        """Search for students within a specific GPA range and display the results."""
        min_grade = float(input("Enter minimum GPA: "))
        max_grade = float(input("Enter maximum GPA: "))
        cursor.execute('SELECT * FROM students WHERE GPA BETWEEN ? AND ?', (min_grade, max_grade))
        filtered_students = cursor.fetchall()
        print("Students with GPA in the specified range:")
        table = PrettyTable(["Email", "Names", "course Name", "Trimester", "grades", "GPA", "Ranking"])
        for student in filtered_students:
            table.add_row([student[0], student[1], student[2]])
        print(table)
        return filtered_students

    def generate_transcript(self):
        """Generate and print the transcript for all students."""
        for student in self.student_list:
            print(f"Transcript for {student.names} ({student.email}):")
            cursor.execute('SELECT course_name, grade FROM registrations WHERE student_email = ?', (student.email,))
            registrations = cursor.fetchall()
            table = PrettyTable(["Course Name", "Trimester", "Grade"])
            for course_name, grade in registrations:
                cursor.execute('SELECT trimester FROM courses WHERE name = ?', (course_name,))
                trimester = cursor.fetchone()[0]
                table.add_row([course_name, trimester, grade])
            print(table)
            print(f"GPA: {student.GPA}\n")

    def update_student(self):
        """Update the information of an existing student."""
        email = input("Enter the email of the student to update: ")
        student = next((s for s in self.student_list if s.email == email), None)
        
        if student:
            new_names = input(f"Enter new names for {student.names} (press Enter to keep current): ")
            if new_names:
                student.names = new_names
                cursor.execute('UPDATE students SET names = ? WHERE email = ?', (new_names, email))
                
            new_email = input(f"Enter new email for {email} (press Enter to keep current): ")
            if new_email:
                cursor.execute('UPDATE students SET email = ? WHERE email = ?', (new_email, email))
                # Update in-memory list
                student.email = new_email
                self.student_list = [s for s in self.student_list if s.email != email]  # Remove old entry
                self.student_list.append(student)  # Add updated entry
                
            conn.commit()
            print("Student information updated successfully.")
        else:
            print("Student not found.")

    def delete_student(self):
        """Delete a student from the grade book."""
        email = input("Enter the email of the student to delete: ")
        student = next((s for s in self.student_list if s.email == email), None)
        
        if student:
            # Delete student from the database
            cursor.execute('DELETE FROM students WHERE email = ?', (email,))
            # Delete student registrations from the database
            cursor.execute('DELETE FROM registrations WHERE student_email = ?', (email,))
            # Update in-memory list
            self.student_list = [s for s in self.student_list if s.email != email]
            conn.commit()
            print("Student deleted successfully.")
        else:
            print("Student not found.")
    
    def view_student(self):
        """View the information of a specific student."""
        email = input("Enter the email of the student to view: ")
        student = next((s for s in self.student_list if s.email == email), None)
        
        if student:
            print(f"Student Information for {student.names} ({student.email}):")
            print(f"Courses Registered:")
            table = PrettyTable(["Course Name", "Trimester", "Grade"])
            for course, grade in student.courses_registered:
                table.add_row([course.name, course.trimester, grade])
            print(table)
            print(f"GPA: {student.GPA}")
        else:
            print("Student not found.")
    
    def view_all_students(self):
        """View all students in the database in a tabular form."""
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
        table = PrettyTable()
        table.field_names = ["Email", "Names", "GPA"]
        for student in students:
            table.add_row([student[0], student[1], student[2]])
        print(table)

def main():
    grade_book = GradeBook()

    # Load data from the database
    cursor.execute('SELECT * FROM students')
    for row in cursor.fetchall():
        student = Student(row[0], row[1])
        student.GPA = row[2]
        cursor.execute('SELECT course_name, grade FROM registrations WHERE student_email = ?', (row[0],))
        for course_name, grade in cursor.fetchall():
            cursor.execute('SELECT * FROM courses WHERE name = ?', (course_name,))
            course_row = cursor.fetchone()
            if course_row:
                course = Course(course_row[0], course_row[1], course_row[2])
                student.courses_registered.append((course, grade))
        grade_book.student_list.append(student)

    cursor.execute('SELECT * FROM courses')
    for row in cursor.fetchall():
        course = Course(row[0], row[1], row[2])
        grade_book.course_list.append(course)

    print("\n----------------------------------------------------")
    print("------------- Welcome to Grade Book App ------------ ")
    print("----------------------------------------------------")

    while True:
        print("\nGrade Book Menu:")
        print("1. Add Student")
        print("2. Add Course")
        print("3. Register Student for Course")
        print("4. Calculate Ranking")
        print("5. Search Students by GPA")
        print("6. Generate Transcript")
        print("7. Update Student")
        print("8. Delete Student")
        print("9. View Menu")
        print("10. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            grade_book.add_student()
        elif choice == "2":
            grade_book.add_course()
        elif choice == "3":
            grade_book.register_student_for_course()
        elif choice == "4":
            grade_book.calculate_ranking()
        elif choice == "5":
            grade_book.search_by_grade()
        elif choice == "6":
            grade_book.generate_transcript()
        elif choice == "7":
            grade_book.update_student()
        elif choice == "8":
            grade_book.delete_student()
        elif choice == "9":
            view_menu(grade_book)
        elif choice == "10":
            break
        else:
            print("Invalid option, please try again.")

def view_menu(grade_book):
    while True:
        print("\nView Menu:")
        print("1. View Student")
        print("2. View All Students")
        print("3. Back to Main Menu")

        choice = input("Choose an option: ")

        if choice == "1":
            grade_book.view_student()
        elif choice == "2":
            grade_book.view_all_students()
        elif choice == "3":
            break
        else:
            print("Invalid option, please try again.")

if __name__ == "__main__":
    main()

