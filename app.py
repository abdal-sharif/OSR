from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="osr"
    )

def generate_student_id(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM student_id_tracker LIMIT 1")
    result = cursor.fetchone()
    last_id = result[0]
    new_id = last_id + 1
    cursor.execute("UPDATE student_id_tracker SET id = %s WHERE id = %s", (new_id, last_id))
    conn.commit()
    cursor.close()
    return f"S{new_id:06d}"

def generate_teacher_id(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teacher_id_tracker LIMIT 1")
    result = cursor.fetchone()
    last_id = result[0]
    new_id = last_id + 1
    cursor.execute("UPDATE teacher_id_tracker SET id = %s WHERE id = %s", (new_id, last_id))
    conn.commit()
    cursor.close()
    return f"T{new_id:06d}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if len(phone) != 9 or not phone.isdigit():
            flash('Phone number must be exactly 9 digits.')
            return redirect(url_for('register'))
        if ' ' in username:
            flash('Username must not contain spaces.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='sha256')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (full_name, phone, username, password, role) VALUES (%s, %s, %s, %s, %s)", 
                       (full_name, phone, username, hashed_password, role))
        conn.commit()
        cursor.close()
        conn.close()

        flash('User created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/teachers')
def teachers():
    if 'role' in session and session['role'] == 'administrator':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM teachers")
        teachers = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('teachers.html', teachers=teachers)
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('home'))

@app.route('/edit_teacher/<id>', methods=['GET', 'POST'])
def edit_teacher(id):
    if 'role' in session and session['role'] == 'administrator':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form['phone']
            education = request.form['education']
            salary = request.form['salary']
            subjects = request.form['subjects']

            cursor.execute("""
                UPDATE teachers
                SET full_name = %s, email = %s, phone = %s, education = %s, salary = %s, subjects = %s
                WHERE id = %s
            """, (full_name, email, phone, education, salary, subjects, id))

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('teachers'))

        cursor.execute("SELECT * FROM teachers WHERE id = %s", (id,))
        teacher = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('edit_teacher.html', teacher=teacher)
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('home'))

@app.route('/delete_teacher/<id>', methods=['POST'])
def delete_teacher(id):
    if 'role' in session and session['role'] == 'administrator':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teachers WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('teachers'))
    else:
        flash("You don't have permission to perform this action.")
        return redirect(url_for('home'))

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if 'role' in session and session['role'] == 'administrator':
        if request.method == 'POST':
            conn = get_db_connection()
            id = generate_teacher_id(conn)
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form['phone']
            education = request.form['education']
            salary = request.form['salary']
            subjects = request.form['subjects']

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO teachers (id, full_name, email, phone, education, salary, subjects)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id, full_name, email, phone, education, salary, subjects))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('teachers'))

        return render_template('add_teacher.html')
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('home'))

@app.route('/students')
def students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('students.html', students=students)

@app.route('/edit_student/<id>', methods=['GET', 'POST'])
def edit_student(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        student_class = request.form['class']
        parents_number = request.form['parents_number']

        if len(phone) != 9 or not phone.isdigit() or len(parents_number) != 9 or not parents_number.isdigit():
            flash("Phone number and Parents' number must be exactly 9 digits.")
            return redirect(url_for('edit_student', id=id))

        cursor.execute("""
            UPDATE students
            SET full_name = %s, email = %s, phone = %s, gender = %s, class = %s, parents_number = %s
            WHERE id = %s
        """, (full_name, email, phone, gender, student_class, parents_number, id))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('students'))

    cursor.execute("SELECT * FROM students WHERE id = %s", (id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<id>', methods=['POST'])
def delete_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('students'))

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        conn = get_db_connection()
        id = generate_student_id(conn)
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        student_class = request.form['class']
        parents_number = request.form['parents_number']

        if len(phone) != 9 or not phone.isdigit() or len(parents_number) != 9 or not parents_number.isdigit():
            flash("Phone number and Parents' number must be exactly 9 digits.")
            return redirect(url_for('add_student'))

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (id, full_name, email, phone, gender, class, parents_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id, full_name, email, phone, gender, student_class, parents_number))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('students'))

    return render_template('add_student.html')

@app.route('/add_exam', methods=['GET', 'POST'])
def add_exam():
    # Only teachers and administrators can add exams
    if 'role' in session and session['role'] in ['administrator', 'teacher']:
        if request.method == 'POST':
            # Handle adding an exam
            flash("Exam added successfully.")
            return redirect(url_for('home'))
        return render_template('add_exam.html')
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('home'))

@app.route('/add_result', methods=['GET', 'POST'])
def add_result():
    # Only teachers and administrators can add results
    if 'role' in session and session['role'] in ['administrator', 'teacher']:
        if request.method == 'POST':
            # Handle adding a result
            flash("Result added successfully.")
            return redirect(url_for('home'))
        return render_template('add_result.html')
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
