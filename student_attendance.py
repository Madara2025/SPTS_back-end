from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

std_att = Blueprint('attendance', __name__)

# Get own class student
@std_att.route('/students/class/<int:class_id>', methods=['GET'])
def get_students_by_class(class_id):
   
    logging.info(f"Request received for students in Class_ID: {class_id}")

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor() 

        
        query = """
            SELECT
                s.student_id,
                s.Index_number AS index_number,
                s.Last_name AS student_last_name,
                s.Other_names AS student_other_names,
                c.Grade AS grade,
                c.Class_name AS class_name
            FROM
                student s
            JOIN
                Class c ON s.Class_ID = c.Class_ID
            WHERE
                s.Class_ID = %s
            ORDER BY
                s.Index_number;
        """
        cursor.execute(query, (class_id,))
        students_data = cursor.fetchall()

        class_studentslist = []
        for student_row in students_data:
            class_studentslist.append({
                'student_id': student_row[0],
                'index_number': student_row[1],
                'student_last_name': student_row[2],
                'student_other_names': student_row[3],
                'grade': student_row[4],
                'class_name': student_row[5]
            })
            print(class_studentslist)

        if not students_data:
            logging.info(f"No students found for Class_ID: {class_id}.")
            return jsonify({"message": f"No students found for Class ID {class_id}"}), 200

        logging.info(f"Successfully retrieved {len(class_studentslist)} students for Class_ID: {class_id}.")
        return jsonify(class_studentslist), 200

    except Exception as e:
        logging.error(f"Error fetching students for Class_ID {class_id} {e}", exc_info=True)
        
        return jsonify({"error": "Internal server error while fetching student data."}), 500
    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed.')
        if connection:
            connection.close()
            logging.info('Database connection closed.')

# Add student attendace to the database
@std_att.route('/attendance', methods=['POST'])
def add_attendance():
    logging.info("Request received to add attendance.")
    
    data = request.get_json()
    logging.info(f'Received data: {data}')

    if not data:
        logging.warning("No JSON data received in POST request for attendance.")
        return jsonify({"error": "Request must contain JSON data."}), 400
    
    required_fields = ['student_id', 'date', 'status', 'Classteacher_ID']
    for field in required_fields:
        if field not in data:
            logging.warning(f"Missing required field: '{field}' in attendance data.")
            return jsonify({"error": f"Missing required field: '{field}'."}), 400
    
    student_id = data.get('student_id')
    date_str = data.get('date')
    status_boolean = data.get('status')
    classteacher_id = data.get('Classteacher_ID')

    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logging.warning(f"Invalid date format received: {date_str}. Expected YYYY-MM-DD.")
        return jsonify({"error": "Invalid date format for 'date'. Please use YYYY-MM-DD."}), 400

    # Convert boolean status to string as per database schema (VARCHAR(10))
    status_string = 'Present' if status_boolean else 'Absent'

    connection = None
    cursor = None
    
    try:
        connection = get_db_connection() 
        logging.info('Successfully connected to the database')
        
        cursor = connection.cursor()
        logging.info('Cursor created')

        cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = %s AND date = %s", (student_id, attendance_date))
        existing_record = cursor.fetchone()

        if existing_record:
            logging.warning(f"Attendance for student_id {student_id} on {date_str} already exists.")
            return jsonify({"error": f"Attendance for student ID {student_id} on {date_str} already exists."}), 409
        

        insert_query = """
            INSERT INTO attendance (student_id, date, status, Classteacher_ID)
            VALUES (%s, %s, %s, %s)
        """
        attendance_data = (student_id, attendance_date, status_string, classteacher_id)
        
        logging.info(f"Attempting to insert attendance: Student ID={student_id}, Date={attendance_date}, Status='{status_string}', Classteacher_ID={classteacher_id}")
        cursor.execute(insert_query, attendance_data)
        connection.commit() 
        
        logging.info(f"Attendance successfully added for student ID {student_id} on {date_str}.")
        return jsonify({"message": "Attendance record added successfully."}), 201 

    except Exception as e:
        logging.error(f"Error adding attendance: {e}", exc_info=True)

        if connection:
            connection.rollback()
        return jsonify({"error": "Internal server error while adding attendance record."}), 500
    
    finally:
        if cursor:
            cursor.close()
            logging.info('Cursor closed.')
        if connection:
            connection.close()
            logging.info('Database connection closed.')


# The following functions (password, get_students, get_logged_in_user_details,
# class_teacher_auth_required, add_attendance, get_class_attendance_by_date)
# are not included in this response as you requested only the simple GET API.
# If you need them, please refer to the previous detailed response.
