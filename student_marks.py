from flask import Blueprint, jsonify, request
from config import get_db_connection
import bcrypt
import logging
from token_verify import token_required

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

std_marks = Blueprint('marks',__name__)

#Get students in request class
@std_marks.route('/students/class/<int:class_id>', methods = ['GET'])
def get_students(class_id):

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
                    s.Last_name AS last_name,
                    s.Other_names AS other_names,
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
                    'last_name': student_row[2],
                    'other_names': student_row[3],
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
@std_marks.route('/marks', methods=['POST'])
def add_marks():

    logging.info("Request received to add student marks.")

    data = request.get_json()
    logging.info(f'Received data: {data}')

    # Input validation
    if not data:
        logging.warning("No JSON data received in POST request")
        return jsonify({"error": "Request must contain JSON data"}), 400
    
    required_fields = ['student_id', 'subject_id', 'teacher_id', 'marks', 'Term_year']
    for field in required_fields:
        if field not in data:
            logging.warning(f"Missing required field: '{field}'")
            return jsonify({"error": f"Missing required field: '{field}'"}), 400
        
        student_id = data.get('student_id')
        subject_id = data.get('subject_id')
        teacher_id = data.get('teacher_id')
        marks = data.get('marks')
        term_year = data.get('Term_year')

    # Validate marks value
    if not isinstance(marks, (int)) or marks < 0:
        logging.warning(f"Invalid marks value: {marks}")
        return jsonify({"error": "Marks must be a positive number"}), 400
    
    # Validate Term_year format if needed
    if not isinstance(term_year, str) or len(term_year) > 50:
        logging.warning(f"Invalid Term_year format: {term_year}")
        return jsonify({"error": "Term and year must be a string (max 50 chars)"}), 400
    
    connection = None
    cursor = None

    try:
        # Database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        logging.info("Database connection established")

        # Check for existing record
        cursor.execute("SELECT marks_id FROM marks WHERE student_id = %s AND subject_id = %s AND Term_year = %s",
            (student_id, subject_id, term_year)
        )

        if cursor.fetchone():
            logging.warning(f"Marks already exist for student {student_id}, subject {subject_id}, term {term_year}")
            return jsonify({
                "error": f"Marks for this student, subject and term already exist"
            }), 409
        
        # Insert new marks record with term year
        cursor.execute("INSERT INTO marks (student_id, subject_id, teacher_id, marks, Term_year) VALUES (%s, %s, %s, %s, %s)", 
                      (student_id, subject_id, teacher_id, marks, term_year))
        connection.commit()

         # Get the inserted record ID
        marks_id = cursor.lastrowid
        logging.info(f"Successfully added marks with ID: {marks_id}")
        return jsonify({
            "message": "Marks added successfully",
            "marks_id": marks_id,
            "student_id": student_id,
            "subject_id": subject_id,
            "term_year": term_year
        }), 201
    
    except Exception as e:
        logging.error(f"Error adding marks: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        return jsonify({"error": "Failed to add marks", "details": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database resources released")