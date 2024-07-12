from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # replace with your MySQL username
        password="",  # replace with your MySQL password
        database="osr"
    )

def generate_teacher_id(conn):
    cursor = conn.cursor()
    
    # Get the current last ID
    cursor.execute("SELECT id FROM teacher_id_tracker LIMIT 1")
    result = cursor.fetchone()
    last_id = result[0]
    
    # Increment the last ID
    new_id = last_id + 1
    
    # Update the last ID in the tracker table
    cursor.execute("UPDATE teacher_id_tracker SET id = %s WHERE id = %s", (new_id, last_id))
    conn.commit()
    
    cursor.close()
    return f"T{new_id}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/students')
def students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('students.html', students=students)

@app.route('/teachers')
def teachers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teachers")
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teachers.html', teachers=teachers)

@app.route('/edit_teacher/<id>', methods=['GET', 'POST'])
def edit_teacher(id):
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

@app.route('/delete_teacher/<id>', methods=['POST'])
def delete_teacher(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teachers WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('teachers'))

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
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

if __name__ == '__main__':
    app.run(debug=True)
