from flask import Blueprint, request, jsonify
from config import get_db_connection
import jwt, os
import datetime, logging, bcrypt
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

Secret_Key = os.getenv('token_secret') 

log_bp = Blueprint('login', __name__)

def create_token(user_id,user_name,user_type):
            token = jwt.encode({
                        'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2),
                        'user_id': user_id,
                        'user_name': user_name,
                        'user_type': user_type }, Secret_Key, algorithm ='HS256')
                        
            logging.info(f"Token genarate using User Id: {user_id} , User name: {user_name}, Type: {user_type}")
            return token


@log_bp.route('/login', methods=['POST'])
def login():
            
            logging.info("Received a POST request for /login")
            data = request.get_json()
            user_name = data.get('user_name') # asign value from front end json object
            password = data.get('password')

            if not user_name or not password:
                  logging.warning("Email and Password are required")
                  return jsonify({"error": "Email and Password are required"}), 400
            
            connection = None
            cursor = None

            try:
                  connection = get_db_connection()
                  if connection is None:
                        logging.error("Databassee connection is failed")
                        return jsonify({"error": "Databassee connection is failed"}), 500
                  
                  cursor = connection.cursor()
                  
                  # --- Attempt to authenticate as a Teacher ---
                  logging.info(f"Try to log in {user_name} as a teacher...")

                  # Query the 'teacher_login' table, joining with 'teacher' table to get role
                  cursor.execute(
                  "SELECT tl.teacher_id, tl.user_name, tl.hashed_password, tl.permission, t.role "
                  "FROM teacher_login tl INNER JOIN teacher t ON tl.teacher_id = t.teacher_id "
                  "WHERE tl.user_name = %s", (user_name,)
                  )

                  teacher_user = cursor.fetchone() # Fetch the first matching teacher record

                  if teacher_user:
                              teacher_id, teacher_username, hashed_password, permission, role = teacher_user
                              logging.info(f"Teacher found: {teacher_username} with permission: {permission}")

                              if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):

                                    if permission == "TRUE":
                                          # If password is correct and permission is true, create a token for the teacher
                                          token = create_token(teacher_id, teacher_username, role) # Pass 'teacher' as user_type

                                          # Store the newly generated token in the 'teacher_login' table
                                          cursor.execute("UPDATE teacher_login SET jwt_token = %s WHERE teacher_id = %s", (token, teacher_id))
                                          connection.commit() # Commit the changes to the database
                              
                                          logging.info(f"Teacher token stored in database for User ID: {teacher_id}")
                                          logging.info(f"Login successful for Teacher User ID: {teacher_id}") 

                                          # Return a success response with user details and the token
                                          return jsonify({
                                          "message": "Login successful", 
                                          "user": {
                                          "user_id": teacher_id, 
                                          "user_name": teacher_username, 
                                          "permission": permission, 
                                          "role": role,
                                          },
                                          "token": token
                                          }), 200
                              
                                    else:
                                     # If teacher account does not have permission
                                     logging.warning(f"Access denied for teacher user ID: {teacher_id} - Account permission is FALSE.")
                                    return jsonify({"error":"You don't have permission to log in"}), 403
                              else:
                                    # If password does not match
                                    logging.warning(f"Invalid password for teacher user: {user_name}.")
                                    return jsonify({"error":"Invalid user name or password"}), 401
            
                  logging.info(f"Teacher login failed for {user_name}. Try to log in as a student...")
                  cursor.execute(
                        "SELECT student_id , user_name, hashed_password, permission " 
                        "FROM student_login WHERE user_name = %s", (user_name,)
                  )
                  student_user = cursor.fetchone()

                  if student_user:
                        # Ensure the unpacking matches the columns selected in the query
                        student_id, student_username, hashed_password, permission = student_user
                        logging.info(f"Student found: {student_username} with permission: {permission}")
                       
                        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                              if permission == "TRUE":
                              # If password is correct, create a token for the student
                                    token = create_token(student_id, student_username, 'student') 

                              # Store the newly generated token in the 'student_login' table
                                    cursor.execute("UPDATE student_login SET jwt_token = %s WHERE student_id = %s", (token, student_id))
                                    connection.commit() 
                  
                                    logging.info(f"Student token stored in database for User ID: {student_id}")
                                    logging.info(f"Login successful for Student User ID: {student_id}") 

                                    # Return a success response with student details and the token
                                    return jsonify({
                                    "message": "Login successful", 
                                    "user": {
                                    "user_id": student_id, 
                                    "user_name": student_username, 
                                    "permission": permission, 
                                    "role": 'student',
                                     },
                                    "token": token
                                    }), 200
                         
                              else:
                                     # If student account does not have permission
                                     logging.warning(f"Access denied for teacher user ID: {student_id} - Account permission is FALSE.")
                                     return jsonify({"error":"You don't have permission to log in"}), 403
                        else:
                         # If password does not match for student
                         logging.warning(f"Invalid password for student user: {user_name}.")
                         return jsonify({"error":"Invalid user name or password"}), 401
                  else:
                        # If the user_name was not found in either the teacher or student tables
                        logging.warning(f"Login failed: User '{user_name}' not found in teacher or student records.")
                        return jsonify({"error":"Invalid user name or password"}), 401
            
            except Exception as e:
                
                  logging.error(f"An unexpected error occurred during login: {e}", exc_info=True) 
                  return jsonify({"error": "An unexpected error occurred during login"}), 500
            finally:
                
                  if cursor:
                        cursor.close()
                        logging.info('Database cursor closed.')
                  if connection:
                        connection.close()
                        logging.info('Database connection closed.')

            