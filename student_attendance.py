from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging

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
                'student_id': student_row['student_id'],
                'index_number': student_row['index_number'],
                'student_last_name': student_row['student_last_name'],
                'student_other_names': student_row['student_other_names'],
                'grade': student_row['grade'],
                'class_name': student_row['class_name']
            })

        if not students_data:
            logging.info(f"No students found for Class_ID: {class_id}.")
            return jsonify({"message": f"No students found for Class ID {class_id}"}), 200

        logging.info(f"Successfully retrieved {len(students_data)} students for Class_ID: {class_id}.")
        return jsonify(students_data), 200

    except Exception as e:
        logging.error(f"Error fetching students for Class_ID {class_id} {e}", exc_info=True)
        # Return a generic server error message, detailed error logged internally
        return jsonify({"error": "Internal server error while fetching student data."}), 500
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
