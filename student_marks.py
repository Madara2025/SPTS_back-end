from flask import Blueprint, jsonify, request
from config import get_db_connection
import bcrypt
import logging
from token_verify import token_required

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

std_marks = Blueprint('marks',__name__)

#get teacher subject and classes
@std_marks.route('/teacher/<int:teacher_id>', methods = ['GET'])
def get_subject(teacher_id):

    logging.info(f"Get all students from GET request for /teacher") 
    
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT sa.subject_id, 
                    sa.assignment_id, 
                    sa.teacher_id, 
                    sa.class_id, 
                    su.subject_name,
                    su.Medium,
                    c.grade, 
                    c.Class_name 
            FROM subjectassignment sa  
            JOIN class c ON sa.class_id = c.class_id 
            JOIN subject su ON sa.subject_id = su.subject_id
            WHERE sa.teacher_id= %s
            ORDER BY sa.class_id;
        """, (teacher_id,))

        results = cursor.fetchall()

        if not results:
            logging.info(f"Teacher with ID {teacher_id} not found or has no class data.")
            return jsonify({'error': 'Teacher not found or no data available'}), 404
        
        class_list = [] # create array
        
        for row in results :
            class_list.append({
                'subject_id': row[0],
                'assignment_id': row[1],
                'teacher_id': row[2],
                'class_id': row[3],
                'subject_name': row[4],
                'Medium': row[5],
                'grade': row[6],
                'Class_name': row[7]

            })
            
        logging.info('Class list compiled')
        return jsonify(class_list)
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




#Get students in request class
@std_marks.route('/teacher/subject/<int:class_id>/<int:teacher_id>/<int:subject_id>', methods = ['GET'])
def get_students(class_id,teacher_id,subject_id):

    logging.info(f"Request received for students in Class_ID: {class_id} , {teacher_id}, {subject_id}")

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor() 


        cursor.execute( """
                SELECT 
                        su.subject_id,
                        su.class_id, 
                        su.teacher_id, 
                        st.student_id,
                        s.Index_number, 
                        s.Other_names, 
                        s.Last_name 
                    FROM subjectassignment su 
                    JOIN studentsubject st 
                    ON su.subject_id = st.subject_id 
                    AND su.class_id = st.class_id 
                    JOIN student s 
                    ON st.student_id = s.student_id 
                    WHERE su.class_id = %s and su.teacher_id = %s and su.subject_id = %s
                ORDER BY
                    s.Index_number;
            """,(class_id,teacher_id,subject_id),)

        students_data = cursor.fetchall()

        class_studentslist = []
        for student_row in students_data:
                class_studentslist.append({
                    'subject_id': student_row[0],
                    'teacher_id': student_row[2],
                    'index_number': student_row[4],
                    'last_name': student_row[6],
                    'other_names': student_row[5],
                    'student_id': student_row[3],
                    
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




# Add student marks to the database
@std_marks.route('/marks', methods=['POST'])

def add_marks():
    logging.info("Request received to add student marks.")
    all_marks = request.get_json()
    logging.info(f'Received data: {all_marks}')

    # Input validation
    if not all_marks:
        logging.warning("No JSON data received in POST request")
        return jsonify({"error": "Request must contain JSON data"}), 400
    # Added: Ensure the received data is a list as expected for multiple mark entries
    if not isinstance(all_marks, list):
        logging.warning("Invalid data format. Expected a list of mark objects.")
        return jsonify({"error": "Invalid data format. Expected a list."}), 400

    connection = None
    cursor = None
    inserted_marks_ids = [] # To store IDs of  inserted marks

    try:
        # Database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        logging.info("Database connection established")

        # Iterate through each individual mark entry in the list
        for data in all_marks:
            required_fields = ['student_id', 'subject_id', 'teacher_id', 'marks', 'Term_year']

            # Corrected: Check if all required fields are present in the current 'data' dictionary
            if not all(field in data for field in required_fields):
                logging.warning(f"Missing required fields in entry: {data}. Skipping this entry.")
                continue # Skip this wrong entry and proceed to the next

            # fields for the current 'data' entry (MOVED INSIDE THE LOOP)
            student_id = data.get('student_id')
            subject_id = data.get('subject_id')
            teacher_id = data.get('teacher_id')
            marks = data.get('marks')
            term_year = data.get('Term_year') 

            # Validate marks value for the current 'data' entry (MOVED INSIDE THE LOOP)
            # Assuming marks can be 0 and up to 100.
            if not isinstance(marks, (int, float)) or not (0 <= marks <= 100):
                logging.warning(f"Invalid marks value for student {student_id}: {marks}. Skipping this entry.")
                continue

            # Validate Term_year format for the current 'data' entry (MOVED INSIDE THE LOOP)
            if not isinstance(term_year, str) or len(term_year) > 50:
                logging.warning(f"Invalid Term_year format for student {student_id}: {term_year}. Skipping this entry.")
                continue
            
            # Insert new marks record with term year for the CURRENT entry
            cursor.execute("INSERT INTO marks (student_id, subject_id, teacher_id, marks, Term_year) VALUES (%s, %s, %s, %s, %s)", 
                           (student_id, subject_id, teacher_id, marks, term_year))
            
            # Get the inserted record ID for the CURRENT entry
            marks_id = cursor.lastrowid
            inserted_marks_ids.append({
                "marks_id": marks_id,
                "student_id": student_id,
                "subject_id": subject_id,
                "term_year": term_year
            })
            logging.info(f"Successfully added marks with ID: {marks_id} for student {student_id}")
        
        # Commit all insertions at once after the loop, if all individual insertions were successful
        connection.commit()
        logging.info(f"All marks committed successfully. Total {len(inserted_marks_ids)} entries added.")

        return jsonify({
            "message": "Marks added successfully",
            "added_entries": inserted_marks_ids
        }), 201
    
    except Exception as e:
        logging.error(f"Error adding marks: {str(e)}", exc_info=True)
        if connection:
            connection.rollback() # Rollback all insertions if any error occurs
        return jsonify({"error": "Failed to add marks", "details": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logging.info("Database resources released")
