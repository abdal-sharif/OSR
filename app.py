from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(minutes=30)  # Session timeout period

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="osr"
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if ' ' in username:
            flash('Username must not contain spaces.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                       (username, hashed_password, role))
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
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND role = %s", (username, role))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.permanent = True  # Make the session permanent so it lasts longer than a browser session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'administrator':
                return redirect(url_for('index'))
            elif user['role'] == 'teacher':
                return redirect(url_for('tindex'))
        else:
            flash('Invalid username, password, or role')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' in session and session['role'] == 'administrator':
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/tindex')
def tindex():
    if 'username' in session and session['role'] == 'teacher':
        return render_template('tindex.html')
    else:
        return redirect(url_for('login'))

# Additional routes for teachers, students, exams, results, etc.
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
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if 'role' in session and session['role'] == 'administrator':
        if request.method == 'POST':
            conn = get_db_connection()
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form['phone']
            education = request.form['education']
            salary = request.form['salary']
            subjects = request.form['subjects']

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO teachers (full_name, email, phone, education, salary, subjects)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, education, salary, subjects))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('teachers'))

        return render_template('add_teacher.html')
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))

@app.route('/students')
def students():
    if 'username' in session:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('students.html', students=students)
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))

@app.route('/edit_student/<id>', methods=['GET', 'POST'])
def edit_student(id):
    if 'username' in session:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form['phone']
            gender = request.form['gender']
            student_class = request.form['class']
            parents_number = request.form['parents_number']

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
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))

@app.route('/delete_student/<id>', methods=['POST'])
def delete_student(id):
    if 'username' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('students'))
    else:
        flash("You don't have permission to perform this action.")
        return redirect(url_for('index'))

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'username' in session:
        if request.method == 'POST':
            conn = get_db_connection()
            full_name = request.form['full_name']
            email = request.form['email']
            phone = request.form['phone']
            gender = request.form['gender']
            student_class = request.form['class']
            parents_number = request.form['parents_number']

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (full_name, email, phone, gender, class, parents_number)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, gender, student_class, parents_number))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('students'))

        return render_template('add_student.html')
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))

@app.route('/add_exam', methods=['GET', 'POST'])
def add_exam():
    if 'role' in session and session['role'] in ['administrator', 'teacher']:
        if request.method == 'POST':
            # Handle adding an exam
            flash("Exam added successfully.")
            return redirect(url_for('index'))
        return render_template('add_exam.html')
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))

@app.route('/add_result', methods=['GET', 'POST'])
def add_result():
    if 'role' in session and session['role'] in ['administrator', 'teacher']:
        if request.method == 'POST':
            # Handle adding a result
            flash("Result added successfully.")
            return redirect(url_for('index'))
        return render_template('add_result.html')
    else:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))
    


@app.route('/add_result')
def result():
    return render_template('add_result.html')

if __name__ == '__main__':
    app.run(debug=True)
