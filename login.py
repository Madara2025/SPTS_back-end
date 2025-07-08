from flask import Blueprint, request, jsonify
from config import get_db_connection
import jwt, os
import datetime, logging, bcrypt
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

Secret_Key = os.getenv('token_secret') 

log_bp = Blueprint('login', __name__)

def create_token(user_id,user_name):
            Token = jwt.encode({
                         'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15),
                         'user_id': user_id,
                         'user_name': user_name}, Secret_Key, algorithm ='HS256')
            logging.info(f"Token genarate using User Id: {user_id} and User name: {user_name}")
            return Token

@log_bp.route('/login', methods=['POST'])
def login():
            
            logging.info("Received a POST request for /login")
            data = request.get_json()
            user_name = data.get('user_name') # asign value from front end json object
            password = data.get('password')

            print(password)

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
                  cursor.execute("SELECT teacher_login.teacher_id, teacher_login.user_name, teacher_login.hashed_password, teacher_login.permission, teacher.role FROM teacher_login INNER JOIN teacher ON teacher_login.teacher_id = teacher.teacher_id WHERE teacher_login.user_name = %s", (user_name))
                  user = cursor.fetchone()

                  if user:
                        teacher_id, user_name, hashed_Password, permission, role = user
                     
                        logging.info(f"User found:{user_name} with permission:{permission}")

                        if bcrypt.checkpw(password.encode('utf-8'), hashed_Password.encode('utf-8')):
                              if permission == "TRUE":
                                 token = create_token(teacher_id,user_name)

                                 #Store token in database
                                 cursor.execute("UPDATE teacher_login SET jwt_token = %s WHERE teacher_id = %s", (teacher_id))
                                 connection.commit()
                                 logging.info(f"Token stored database for User ID:{teacher_id}")
                                 logging.info(f"Login Successful for User ID:{teacher_id}") 

                                 return jsonify({"message": "Login successful", 
                                                 "user": {"teacher_id":teacher_id, "user_name":user_name, "permission":permission, "role":role} ,
                                                 "token": token}), 200
                  
                              else:
                                    logging.warning(f"Don't have permission for user ID: {teacher_id} - Account permission FALSE")
                                    return jsonify({"error":"You don't have permission"}), 403
                        else:
                              logging.warning(f"Invalid password for password: {password}")
                              return jsonify({"error":"Inavalid user name or password"}), 401
                  else:
                        logging.warning(f"Invalid user name: {teacher_id} - User not found")
                        return jsonify({"error":"Inavalid user name or password"}), 401
                  
                  
            except Exception as e:
                              logging.error(f"Login error: {e}")
                              return jsonify({"error": "An unexpected error occurred"}), 500
            finally:
                  if cursor:
                        cursor.close()
                        logging.info('Cursor closed.')
                  if connection:
                        connection.close()
                        logging.info('Database connection closed.')


