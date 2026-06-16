import mysql.connector
global cnx
global isInserted

#Create a connection to the database
cnx = mysql.connector.connect(
    host="localhost", 
    user="root", 
    password="2000414759", 
    database="quizo"
)

def get_all_details():
    cursor = cnx.cursor()

    query = ("SELECT * FROM quizo.sign_up")
    cursor.execute(query)

    rows = cursor.fetchall()

    for row in rows:
        print(row)
    cursor.close()
    return

def insert_signup(email, username, password):
    try:
        #Create a cursor object
        cursor = cnx.cursor()

        query = "INSERT INTO quizo.sign_up (email, username, password) VALUES (%s, %s, %s)"
        # query2 = "INSERT INTO quizo.login_credentials () VALUES ()"
        
        cursor.execute(query, (email, username, password))
        cnx.commit()
        cursor.close()
        print("Sign-Up data credentials inserted successfully!")
        return 1

    except mysql.connector.Error as err:
        print("Error inserting the order item:", err)
        #Rollback changes if necessary
        cnx.rollback()
        return -1
    
    except Exception as e:
        print(f"An error occurred: {e}")
        #Rollback changes if necessary
        cnx.rollback()
        return -1
    return None

def search_login_credentials(email, password):
    #Create a cursor object
    cursor = cnx.cursor()

    query = ("SELECT email,password FROM quizo.sign_up where email=%s and password=%s")
    cursor.execute(query, (email, password))
    rows = cursor.fetchall()
    cursor.close()
    if rows:
        print("Data found")
        return True
    else:
        print("No data found.")
    return False


def create_exam(title, password, questions_json, duration, created_by):
    try:
        cursor = cnx.cursor()
        query = "INSERT INTO quizo.exams (title, password, questions, duration, created_by) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(query, (title, password, questions_json, duration, created_by))
        cnx.commit()
        exam_id = cursor.lastrowid
        cursor.close()
        return exam_id
    except Exception as e:
        print(f"Error creating exam: {e}")
        cnx.rollback()
        return None

def _get_cursor():
    try:
        cnx.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        pass
    return cnx.cursor(dictionary=True)

def get_exam_by_password(password):
    cursor = _get_cursor()
    cursor.execute("SELECT * FROM quizo.exams WHERE password=%s", (password,))
    row = cursor.fetchone()
    cursor.close()
    return row

def get_exam_by_id(exam_id):
    cursor = _get_cursor()
    cursor.execute("SELECT * FROM quizo.exams WHERE id=%s", (exam_id,))
    row = cursor.fetchone()
    cursor.close()
    return row

def save_exam_result(exam_id, student_name, score, total, violations, cheat_events_json):
    try:
        cursor = _get_cursor()
        query = """INSERT INTO quizo.exam_results
                   (exam_id, student_name, score, total, violations, cheat_events)
                   VALUES (%s,%s,%s,%s,%s,%s)"""
        cursor.execute(query, (exam_id, student_name, score, total, violations, cheat_events_json))
        cnx.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error saving result: {e}")
        cnx.rollback()
        return False

def get_exam_results(exam_id):
    cursor = _get_cursor()
    cursor.execute(
        "SELECT id, student_name, score, total, violations, cheat_events, submitted_at "
        "FROM quizo.exam_results WHERE exam_id=%s ORDER BY submitted_at DESC",
        (exam_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows

def get_exams_by_user(email):
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("SELECT id, title, password, duration, created_at FROM quizo.exams WHERE created_by=%s ORDER BY created_at DESC", (email,))
    rows = cursor.fetchall()
    cursor.close()
    return rows

if __name__ == "__main__":
    print(get_all_details())
    # print(search_login_credentials('kumar1166@gmail.com', 'Kris@2223'))
    # insert_signup('kumar1166@gmail.com', 'kris6', 'Kris@2223')
    # print(get_all_details())