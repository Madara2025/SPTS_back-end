from flask import Blueprint, jsonify, request
from config import get_db_connection
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

usr = Blueprint('user',__name__)

def password(parent_nic):
    return hashlib.sha512(parent_nic.encode()).hexdigest()


#get all students

@usr.route('/students', methods = ['GET'])
def get_students():

    logging.info('Get all students')
    
    connection = None
    cursor = None

    try:

        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')

        cursor.execute("SELECT * FROM student JOIN student_login ON student.index_number = student_login.index_number")
        students = cursor.fetchall()
        logging.info(f'Retrieved {len(students)} students from the database')

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
                'class_id': row[12],
                'permission': row[13]
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
def add_students():

    logging.info('Entering add_students() - Adding a new student')

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

        hashed_password = password('parent_nic')
        logging.info(f'Hashed password for parent_nic: {parent_nic}')

        cursor.execute("INSERT INTO student (last_name, other_names, address, email, date_of_birth, parent_name, gender, contact_number, parent_nic, user_name, index_number, class_id)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (last_name, other_names, address, email, date_of_birth, parent_name, gender, contact_number, parent_nic, user_name, index_number, class_id))
        logging.info('Inserted student data into student table')

        cursor.execute("INSERT INTO student_login (index_number, user_name, hashed_password, permission ) VALUES (%s, %s, %s, %s)",
                       (index_number, user_name, hashed_password, permission))
        logging.info('Inserted student login data into student_login table')
        
        connection.commit()
        logging.info('Transaction committed successfully')
        
        return  jsonify({'success': 'Student added successfully'}), 201

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
       

#update student
@usr.route('/students/<string:index_number>', methods = ['PUT'])
def update_student(index_number):

    logging.info(f'Entering update_student() - Updating student with index_number: {index_number}')

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
                

        cursor.execute("UPDATE student SET last_name = %s, other_names = %s, address = %s, email = %s, date_of_birth = %s, parent_name = %s, gender = %s, contact_number = %s, parent_nic = %s, user_name = %s, class_id = %s WHERE index_number = %s ", 
                       (last_name, other_names, address, email, date_of_birth, parent_name, gender, contact_number, parent_nic, user_name, index_number, class_id))
        logging.info('Updated student data in student table')
        
 
        cursor.execute("UPDATE student_login SET user_name = %s, permission = %s WHERE index_number = %s", 
                       (user_name, permission, index_number))
        logging.info('Updated student login data in student_login table')

        connection.commit()
        logging.info('Transaction committed successfully')


        return jsonify({'success': 'Student updated successfully'}),201
    
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
def update_Spermission(index_number):

    logging.info(f'Entering update_Spermission() - Changeing permission student with index_number: {index_number}')

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

    logging.info('Get all teachers')

    try:

        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')

        cursor.execute("SELECT teacher.teacher_id, teacher.last_name, teacher.other_names, teacher.address, teacher.email, teacher.date_of_birth, teacher.personal_title, teacher.role, teacher.contact_number, teacher.user_name, teacher.nic_number teacher.emp_id, teacher_login.permission FROM teacher JOIN teacher_login ON teacher.teacher_id = teacher_login.teacher_id")
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

    logging.info('Entering add_teacher() - Adding a new teacher')

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

        hashed_passwovrd = password('nic_number')
        logging.info(f'Hashed password for nic_number: {nic_number}')

        cursor.execute("INSERT INTO teacher (last_name, other_names, address, email, date_of_birth, personal_title, role, contact_number, user_name, nic_number, emp_id)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (last_name, other_names, address, email, date_of_birth, personal_title, role, contact_number, user_name, nic_number, emp_id))
        logging.info('Inserted teacher data into teacher table')

        cursor.execute("INSERT INTO teacher_login (emp_id, user_name, hashed_password, permission ) VALUES (%s, %s, %s, %s)",
                       (emp_id, user_name, hashed_passwovrd, permission))
        logging.info('Inserted teacher login data into teacher_login table')
        
        connection.commit()
        logging.info('Transaction committed successfully')

        
        return  jsonify({'success': 'Teacher added successfully'})

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



#update teacher
@usr.route('/teachers/<int:emp_id>', methods = ['PUT'])
def update_teacher(emp_id):

    logging.info(f'Entering update_teacher() - Updating teacher with emp_id: {emp_id}')

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
        birth_day = data.get('birth_day')
        personal_title = data.get('personal_title')
        role = data.get('role')
        contact_number = data.get('contact_number')
        user_name = data.get('user_name')
        nic_number = data.get('nic_number')
        emp_id = data.get('emp_id')
        permission = data.get('permission')

        cursor.execute("UPDATE teacher SET last_name = %s, other_names = %s, address = %s, email = %s, birth_day = %s, personal_title = %s, role = %s, contact_number = %s, user_name = %s, nic_number = %s, emp_id = %s WHERE emp_id = %s ", 
                       (last_name, other_names, address, email, birth_day, personal_title, role, contact_number, user_name, nic_number, emp_id ))
        logging.info('Updated teacher data in teacher table')

        cursor.execute("UPDATE teacher_login SET user_name = %s, permission = %s WHERE emp_id = %s" , 
                       (user_name, permission, emp_id,))
        logging.info('Updated teacher login data in teacher_login table')

        connection.commit()
        logging.info('Transaction committed successfully')

        return jsonify({'success': 'teacher updated successfully'}),201
    
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
def update_Tpermission(emp_id):

    logging.info(f'Entering update_Tpermission() - Changeing permission student with emp_id: {emp_id}')

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