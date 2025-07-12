from flask import Blueprint, jsonify, request
from config import get_db_connection
import bcrypt
import logging
from token_verify import token_required

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

usr = Blueprint('user',__name__)

def password_hashed(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password,hashedpw):
    return bcrypt.checkpw(password.encode('utf-8'), hashedpw.encode('utf-8'))



#get all students

@usr.route('/students', methods = ['GET'])

def get_students():

    logging.info(f"Get all students from GET request for /students") 
    
    connection = None
    cursor = None

    try:

        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')

        cursor.execute("SELECT * FROM student JOIN student_login ON student.index_number = student_login.index_number JOIN class ON student.Class_id = class.class_id")
        students = cursor.fetchall()
        logging.info(f'Retrieved {len(students)} students from the database')
        logging.info(f'Compiled Student list{students}')

        student_list = [] # create array
        
        for row in students :
            student_list.append({
                'student_id': row[0],
                'last_name': row[1],
                'other_names': row[2],
                'address': row[3],
                'email': row[4],
                'date_of_birth': row[5],
                'parent_name': row[6],
                'gender': row[7],
                'contact_number': row[8],
                'parent_nic': row[9],
                'user_name': row[10],
                'index_number': row [11],
                'grade': row[20],
                'class_name': row[21],
                'permission': row[18]
            })
            
            
        logging.info('Student list compiled')
        return jsonify(student_list)


    except Exception as e:

        logging.error(f'Error in get_students(): {e}', exc_info=True)
        if connection:        
            connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        
        if cursor:
            cursor.close()
            logging.info('Cursor closed')
        if connection:
            connection.close()
            logging.info('Connection closed')
        

#add student
@usr.route('/students', methods = ['POST'])

def add_students(
    
):

    logging.info('Entering add_students from POST request for /students') 
    connection = None
    cursor = None

    try:
        
        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')

        data = request.get_json()
        logging.info(f'Received data: {data}')

        last_name = data.get('last_name')
        other_names = data.get('other_names')
        address = data.get('address')
        email = data.get('email')
        date_of_birth = data.get('date_of_birth')
        parent_name = data.get('parent_name')
        gender = data.get('gender')
        contact_number = data.get('contact_number')
        parent_nic = data.get('parent_nic')
        user_name = data.get('user_name')
        index_number = data.get('index_number')
        class_id = data.get('class_id')
        permission = data.get('permission')
        hashed_password = password_hashed(parent_nic)
        selected_subjects = data.get('selected_subjects', [])
        logging.info(f'Hashed password for parent_nic: {parent_nic}')

        common_subjects = get_mandatory_subject_ids(cursor)
        
        all_subjects = list(set(selected_subjects + common_subjects))
        logging.info(f"All subjects to enroll (including mandatory): {all_subjects}")
        

        #check student already exists
        cursor.execute("SELECT * FROM student WHERE index_number = %s or email = %s" , (index_number, email))
        exsiting_student = cursor.fetchone()

        if exsiting_student:
            logging.warning(f'Student with index_number{index_number} or email {email} already exists.')
            return jsonify({'error': 'Student with this index number or email already exists'}), 400


        cursor.execute("INSERT INTO student (last_name, other_names, address, email, date_of_birth, parent_name, gender, contact_number, parent_nic, user_name, index_number, class_id)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (last_name, other_names, address, email, date_of_birth, parent_name, gender, contact_number, parent_nic, user_name, index_number, class_id))
        logging.info('Inserted student data into student table')
        connection.commit()
        
        # Retrieve the last inserted student_id
        cursor.execute("SELECT student_id FROM student WHERE user_name = %s AND parent_nic = %s", (user_name, parent_nic))
        connection.commit()

        result = cursor.fetchone() 
        print(result)

        student_id = None
        if result:
            student_id = result[0]         
       
        logging.info(f'Last inserted student_id: {student_id}')

        cursor.execute("INSERT INTO student_login (index_number, user_name, hashed_password, permission,  student_id ) VALUES (%s, %s, %s, %s, %s)",
                       (index_number, user_name, hashed_password, permission, student_id))
        logging.info('Inserted student login data into student_login table')

        for subject_id in all_subjects:
            cursor.execute("INSERT INTO studentsubject (student_id, subject_id, Class_id) VALUES (%s, %s, %s)", (student_id, subject_id, class_id))
            logging.info(f'Linked student {student_id} to subject {subject_id}')
        
        connection.commit()
        logging.info('Transaction committed successfully')
        
        return  jsonify({'success': 'Student added successfully' , 'student_id': student_id}), 201

    except Exception as e:

        logging.error(f'Error in add_students(): {e}', exc_info=True)
        if connection:
            connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:

        if cursor:
            cursor.close()
            logging.info('Cursor closed')
        if connection:
            connection.close()
            logging.info('Connection closed')


#get on student using student_id            
@usr.route('/students/<int:student_id>', methods=['GET'])

def get_student( student_id):
    logging.info(f"GET request for /students/{student_id}")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM student WHERE student_id = %s", (student_id,))
        result = cursor.fetchone()

        if result:
            student = {
                'student_id': result[0],
                'last_name': result[1],
                'other_names': result[2],
                'address': result[3],
                'email': result[4],
                'date_of_birth':str(result[5]) ,
                'parent_name': result[6],
                'gender': result[7],
                'contact_number': result[8],
                'parent_nic': result[9],
                'user_name': result[10],
                'index_number': result [11],
                'class_id': result[12],
                
            }
            return jsonify(student), 200
        else:
            return jsonify({'error': 'Student not found'}), 404

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()       

#update student
@usr.route('/students/<int:student_id>', methods = ['PUT'])

def update_student(student_id):

    logging.info(f'Entering update_student from PUT request for /students/index_number: {student_id}')
    data = request.get_json()
    logging.info(f"Received JSON: {data}")

    last_name = data.get('last_name')
    other_names = data.get('other_names')
    address = data.get('address')
    email = data.get('email')
    date_of_birth = data.get('date_of_birth')
    parent_name = data.get('parent_name')
    gender = data.get('gender')
    contact_number = data.get('contact_number')
    parent_nic = data.get('parent_nic')
    user_name = data.get('user_name')
    index_number = data.get('index_number')
    class_id = data.get('class_id')
    password = data.get('password')

    hashed_pw = None
    if password:
        hashed_pw = password_hashed(password)

    connection = None
    cursor = None
    
    try:
        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')     
                
        cursor.execute("UPDATE student SET last_name = %s, other_names = %s, address = %s, email = %s, date_of_birth = %s, parent_name = %s, gender = %s, contact_number = %s, parent_nic = %s, user_name = %s, index_number = %s, class_id = %s WHERE student_id = %s ", 
                       (last_name, other_names, address, email, date_of_birth, parent_name, gender, contact_number, parent_nic, user_name, index_number, class_id, student_id))
        logging.info('Updated student data in student table')
        

        if hashed_pw:
            cursor.execute("UPDATE student_login SET user_name = %s, hashed_password = %s WHERE student_id = %s", (user_name, hashed_pw, student_id))
        else:
            cursor.execute("UPDATE student_login SET user_name = %s WHERE student_id = %s", (user_name, student_id))
        connection.commit()

        return jsonify({'message': 'Student updated successfully'}), 200

 
    
    except Exception as e:

        logging.error(f'Error in update_student(): {e}', exc_info=True)
        if connection:
         connection.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed')
        if connection:
            connection.close()
            logging.info('Connection closed')

            
#remove student
@usr.route('/students/remove/<string:index_number>', methods=['PUT'])

def update_Spermission( index_number):

    logging.info(f'Entering update_student from PUT request for /students/remove/index_number: {index_number}')

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    permission = data.get('permission')

    try:
        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')

    
        cursor.execute("UPDATE student_login SET permission = %s WHERE index_number = %s", 
                       (permission, index_number))
        

        connection.commit()
        logging.info(f"Student permission for index_number {index_number} updated to '{permission}' successfully")

        return jsonify({'message': 'student permission Removed successfully'}), 200

    except Exception as e:
        logging.error(f'Error in update_studentpermission(): {e}', exc_info=True)
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed')
        if connection:
            connection.close()
            logging.info('Connection closed')



#get all teachers
@usr.route('/teachers', methods = ['GET'])

def get_teachers():

    logging.info(f"Get all Teachers from GET request for /teachers")

    try:

        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')

        cursor.execute("SELECT teacher.teacher_id, teacher.last_name, teacher.other_names, teacher.address, teacher.email, teacher.date_of_birth, teacher.personal_title, teacher.role, teacher.contact_number, teacher.user_name, teacher.nic_number, teacher.emp_id, teacher_login.permission FROM teacher JOIN teacher_login ON teacher.teacher_id = teacher_login.teacher_id")
        teachers = cursor.fetchall()
        logging.info(f'Retrieved {len(teachers)} teachers from the database')


        teacher_list = []

        for row in teachers:
            teacher_list.append({
                'teacher_id': row[0],
                'last_name': row[1],
                'other_names': row[2],
                'address': row[3],
                'email': row[4],
                'date_of_birth': row[5],
                'personal_title': row[6],
                'role': row[7],
                'contact_number': row[8],
                'user_name': row[9],
                'nic_number': row[10],
                'emp_id': row [11],
                'permission': row[12]
            })
            print(teacher_list)

        logging.info('Teacher list compiled')
        return jsonify(teacher_list)
    
    except Exception as e:
        logging.error(f'Error in get_teachers(): {e}', exc_info=True)
        if connection:        
            connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed')
        if connection:
            connection.close()
            logging.info('Connection closed')
        
#add teacher
@usr.route('/teachers', methods = ['POST'])

def add_teacher():

    logging.info('Entering add_teacher from POST request for /teachers') 
    
    try:
        connection = get_db_connection()
        logging.info('Successfully connected to the database')

        cursor = connection.cursor()
        logging.info('Cursor created')

        data = request.get_json()
        logging.info(f'Received data: {data}')

        last_name = data.get('last_name')
        other_names = data.get('other_names')
        address = data.get('address')
        email = data.get('email')
        date_of_birth = data.get('date_of_birth')
        personal_title = data.get('personal_title')
        role = data.get('role')
        contact_number = data.get('contact_number')
        user_name = data.get('user_name')
        nic_number = data.get('nic_number')
        emp_id = data.get('emp_id')
        permission = data.get('permission')
        hashed_password = password_hashed(nic_number)
        
        print(nic_number)

        #check teacher already exists
        cursor.execute("SELECT * FROM teacher WHERE emp_id = %s or email = %s" , (emp_id, email))
        exsiting_teacher = cursor.fetchone()

        if exsiting_teacher:
            logging.warning(f'Teacher with index_number{emp_id} or email {email} already exists.')
            return jsonify({'error': 'Teacher with this employee id or email already exists'}), 400


        cursor.execute("INSERT INTO teacher (last_name, other_names, address, email, date_of_birth, personal_title, role, contact_number, user_name, nic_number, emp_id)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (last_name, other_names, address, email, date_of_birth, personal_title, role, contact_number, user_name, nic_number, emp_id))
        logging.info('Inserted teacher data into teacher table')
        connection.commit()

          # Retrieve the last inserted teacher_id
        cursor.execute("SELECT teacher_id FROM teacher WHERE user_name = %s AND nic_number = %s", (user_name, nic_number))
        connection.commit()

        result = cursor.fetchone() 
    
        teacher_id = None
        if result:
            teacher_id = result[0]

        cursor.execute("INSERT INTO teacher_login (emp_id, user_name, hashed_password, permission, teacher_id ) VALUES (%s, %s, %s, %s, %s)",
                       (emp_id, user_name, hashed_password, permission, teacher_id))
        logging.info('Inserted teacher login data into teacher_login table')
        
        connection.commit()
        logging.info('Transaction committed successfully')
        return  jsonify({'success': 'Teacher added successfully' , 'teacher_id': teacher_id}), 201

    except Exception as e:
        logging.error(f'Error in add_teachers(): {e}', exc_info=True)
        if connection:        
            connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed')

        if connection:
            connection.close()
            logging.info('Connection closed')


#get on teacher using teacher_id            
@usr.route('/teachers/<int:teacher_id>', methods=['GET'])

def get_teacher( teacher_id):
    logging.info(f"GET request for /teachers/{teacher_id}")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM teacher WHERE teacher_id = %s", (teacher_id,))
        result = cursor.fetchone()

        if result:
            teacher = {
                'teacher_id': result[0],
                'last_name': result[1],
                'other_names': result[2],
                'address': result[3],
                'email': result[4],
                'date_of_birth':str(result[5]) ,
                'personal_title': result[6],
                'role': result[7],
                'contact_number': result[8],
                'user_name': result[9],
                'nic_number': result [10],
                'emp_id': result[11],
                
            }
            return jsonify(teacher), 200
        else:
            return jsonify({'error': 'Teacher not found'}), 404

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()    


#update teacher
@usr.route('/teachers/<int:teacher_id>', methods = ['PUT'])

def update_teacher(teacher_id):

    logging.info(f'Entering update_teacher from PUT request for /teachers/teacher_id: {teacher_id}')
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        logging.info('Successfully connected to the database')

        cursor = connection.cursor()
        logging.info('Cursor created')

        data = request.get_json()
        logging.info(f'Received data: {data}')

        emp_id = data.get('emp_id')
        last_name = data.get('last_name')
        other_names = data.get('other_names')
        address = data.get('address')
        email = data.get('email')
        date_of_birth = data.get('date_of_birth')
        personal_title = data.get('personal_title')
        role = data.get('role')
        contact_number = data.get('contact_number')
        user_name = data.get('user_name')
        nic_number = data.get('nic_number')
        emp_id = data.get('emp_id')
        password = data.get('password')

        hashed_pw = None
        if password:
            hashed_pw = password_hashed(password)

        cursor.execute("UPDATE teacher SET emp_id = %s,last_name = %s, other_names = %s, address = %s, email = %s, date_of_birth = %s, personal_title = %s, role = %s, contact_number = %s, user_name = %s, nic_number = %s WHERE teacher_id = %s ", 
                       (emp_id,last_name, other_names, address, email, date_of_birth, personal_title, role, contact_number, user_name, nic_number, teacher_id ))
        logging.info('Updated teacher data in teacher table')

        if hashed_pw:

            cursor.execute("UPDATE teacher_login SET user_name = %s, hashed_password = %s WHERE teacher_id = %s" , 
                       (user_name, hashed_pw, teacher_id,))
            logging.info('Updated teacher login data in teacher_login table')

        else:
            cursor.execute("UPDATE teacher_login SET user_name = %s WHERE teacher_id = %s", (user_name, teacher_id))
        connection.commit()

        return jsonify({'message': 'teacher updated successfully'}), 200

    
    except Exception as e:
        logging.error(f'Error in update_teacher(): {e}', exc_info=True)
        if connection:        
            connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed')

        if connection:
            connection.close()
            logging.info('Connection closed')


#remove teacher
@usr.route('/teachers/remove/<int:emp_id>', methods=['PUT'])

def update_Tpermission( emp_id):

    logging.info(f'Entering update_Tpermission from PUT request for /teachers/remove/emp_id: {emp_id}')

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    permission = data.get('permission')

    try:
        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')
    
        cursor.execute("UPDATE teacher_login SET permission = %s WHERE emp_id = %s", 
                       (permission, emp_id))
      
        connection.commit()
        logging.info(f"Teacher permission for emp_id {emp_id} updated to '{permission}' successfully")


        return jsonify({'message': 'teacher permission Removed successfully'}), 200

    except Exception as e:
        logging.error(f'Error in update_teacherpermission(): {e}', exc_info=True)
        if connection:        
            connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed')

        if connection:
            connection.close()
            logging.info('Connection closed')



# get subjects group vice
@usr.route('/subjects', methods=['GET'])

def get_subjects():
    logging.info("Attempting to retrieve all subjects.")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        logging.info('Successfully connected to the database for subjects.')
        cursor = connection.cursor()
        logging.info('Cursor created for subjects.')

        all_grouped_subjects = {}

        #Fetch Esthetic (C1) subjects
        cursor.execute("SELECT subject_id, Medium, subject_name, subject_category FROM subject WHERE subject_category = 'C1'")
        Esthetic_sub = cursor.fetchall()
        logging.info(f'Retrieved {len(Esthetic_sub)} subjects from the database.')
        logging.info(f'Compiled Esthetic_sub:{Esthetic_sub}')

        esthetic_list = []
        for row in Esthetic_sub:
            esthetic_list.append({
                'subject_id': row[0],
                'medium' : row[1],
                'subject_name': row[2],
                'subject_category':row[3]
            })

            all_grouped_subjects['C1'] = esthetic_list

        #Fetch Science subjects
        cursor.execute("SELECT subject_id, Medium, subject_name, subject_category FROM subject WHERE subject_category = 'Science'")
        Science_sub = cursor.fetchall()
        logging.info(f'Retrieved {len(Science_sub)} subjects from the database.')
        logging.info(f'Compiled Esthetic_sub:{Science_sub}')

        science_list = []
        for row in Science_sub:
            science_list.append({
                'subject_id': row[0],
                'medium' : row[1],
                'subject_name': row[2],
                'subject_category':row[3]
            })

            all_grouped_subjects['Science'] = science_list
            
        #Fetch Maths subjects
        cursor.execute("SELECT subject_id, Medium, subject_name, subject_category FROM subject WHERE subject_category = 'Maths'")
        Maths_sub = cursor.fetchall()
        logging.info(f'Retrieved {len(Maths_sub)} subjects from the database.')
        logging.info(f'Compiled Esthetic_sub:{Maths_sub}')

        maths_list = []
        for row in Maths_sub:
            maths_list.append({
                'subject_id': row[0],
                'medium' : row[1],
                'subject_name': row[2],
                'subject_category':row[3]
            })

            all_grouped_subjects['Maths'] = maths_list

        #Fetch Civc subjects
        cursor.execute("SELECT subject_id, Medium, subject_name, subject_category FROM subject WHERE subject_category = 'Civic'")
        Civic_sub = cursor.fetchall()
        logging.info(f'Retrieved {len(Civic_sub)} subjects from the database.')
        logging.info(f'Compiled Esthetic_sub:{Civic_sub}')

        civic_list = []
        for row in Civic_sub:
            civic_list.append({
                'subject_id': row[0],
                'medium' : row[1],
                'subject_name': row[2],
                'subject_category':row[3]
            })

            all_grouped_subjects['Civic'] = civic_list

        #Fetch Health subjects
        cursor.execute("SELECT subject_id, Medium, subject_name, subject_category FROM subject WHERE subject_category = 'Health'")
        Health_sub = cursor.fetchall()
        logging.info(f'Retrieved {len(Health_sub)} subjects from the database.')
        logging.info(f'Compiled Esthetic_sub:{Health_sub}')

        health_list = []
        for row in Health_sub:
            health_list.append({
                'subject_id': row[0],
                'medium' : row[1],
                'subject_name': row[2],
                'subject_category':row[3]
            })

            all_grouped_subjects['Health'] = health_list
            

        logging.info('Subject list compiled successfully.')
        return jsonify(all_grouped_subjects), 200

    except Exception as e:
        logging.error(f'Error in get_subjects(): {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor for subjects closed.')
        if connection:
            connection.close()
            logging.info('Connection for subjects closed.')

#call common subject
def get_mandatory_subject_ids(cursor):
    
    try:
        cursor.execute("SELECT subject_id FROM subject WHERE subject_category = %s", ('T',))
        common_subjects = [row[0] for row in cursor.fetchall()]

        logging.info(f"Fetched mandatory subjects (T group): {common_subjects}")
        return common_subjects
    
    except Exception as e:
        logging.error(f"Error fetching mandatory subjects: {e}")
        return [] # Return empty list in case of error
