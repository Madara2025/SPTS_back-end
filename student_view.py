from flask import Blueprint, jsonify, request
from config import get_db_connection
import logging
from token_verify import token_required


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

std = Blueprint('get_student',__name__)

@std.route('/student/<int:student_id>', methods=['GET'])

def get_student( student_id):
    logging.info(f"GET request for /student/{student_id}")

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                s.student_id, s.Last_name, s.Other_names, s.Address, s.Email, s.Date_of_birth,
                s.Parent_name, s.Gender, s.Contact_number, s.Parent_nic, s.User_name, s.Index_number,
                s.class_id AS student_class_id, 
                m.subject_id, m.teacher_id, m.Term_year, m.marks, m.marks_id, 
                c.Grade, c.Class_name
            FROM
                student s
            JOIN
                marks m ON s.student_id = m.student_id
            JOIN
                class c ON s.class_id = c.class_id
            WHERE
                s.student_id = %s
            ORDER BY m.Term_year, m.subject_id;
        """, (student_id,))

        results = cursor.fetchall()

        if not results:
            logging.info(f"Student with ID {student_id} not found or has no marks/class data.")
            return jsonify({'error': 'Student Has Not Marks Yet'}), 404

        # Initialize student data structure
        student_data = {
            'student_id': None,
            'last_name': None,
            'other_names': None,
            'address': None,
            'email': None,
            'date_of_birth': None,
            'parent_name': None,
            'gender': None,
            'contact_number': None,
            'parent_nic': None,
            'user_name': None,
            'index_number': None,
            'class_id': None,
            'class_name': None,
            'grade': None,
            'marks': [] #  hold multiple mark 
        }

        # Process the first row to get student and class details
        # Accessing columns by numerical index (less robust than dict(zip()))
        row1 = results[0] 

        student_data['student_id'] = row1[0]
        student_data['last_name'] = row1[1]
        student_data['other_names'] = row1[2]
        student_data['address'] = row1[3]
        student_data['email'] = row1[4]
        student_data['date_of_birth'] = (row1[5]) # Convert date to string use str(row1[5])
        student_data['parent_name'] = row1[6]
        student_data['gender'] = row1[7]
        student_data['contact_number'] = row1[8]
        student_data['parent_nic'] = row1[9]
        student_data['user_name'] = row1[10]
        student_data['index_number'] = row1[11]
        student_data['class_id'] = row1[12] 
        student_data['class_name'] = row1[19] 
        student_data['grade'] = row1[18]     

        # Iterate  all results to get all marks
        for row in results:
            
           student_data['marks'].append({ 
                'marks_id': row[17],    
                'subject_id': row[13],  
                'teacher_id': row[14],  
                'term_year': row[15],  
                'marks': row[16]        
            })
            
        logging.info(f"Successfully get data for student ID: {student_id}")
        return jsonify(student_data), 200

    except Exception as e:
        logging.error(f"Error get student data for ID {student_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal server error occurred', 'details': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
            logging.info('Database cursor closed.')
        if connection:
            connection.close()
            logging.info('Database connection closed.')