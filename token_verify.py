from flask import request, jsonify, Blueprint
import jwt
import logging
from config import get_db_connection
from dotenv import load_dotenv
import os
from functools import wraps

load_dotenv()
SECRET_KEY = os.getenv('token_secret')

token = Blueprint('verify_jwt_token', __name__)

@token.route('/verify-token', methods=['GET'])
def verify_jwt_token():
    token = request.headers.get('Authorization')
    if not token:
        logging.warning("Missing token in request headers")
        return None, jsonify({'error': 'Missing token'}), 401

    if token.startswith("Bearer "):
        token = token[7:]
        
    connection = None
    cursor = None

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = decoded['user_id']
        user_name = decoded['user_name']
        user_type = decoded['user_type']

        if not user_id or not user_name or not user_type:
            logging.warning("Decoded token missing essential fields (user_id, user_name, or user_type)")
            return jsonify({'error': 'Invalid token payload'}), 403
        
        logging.info(f"Token decoded for user ID: {user_id}, user_name: {user_name}, user_type: {user_type}")

        connection = get_db_connection()
        cursor = connection.cursor()

        token_valid = False

        staff_roles = ['teacher', 'principal', 'admin']
        if user_type in staff_roles:
       
            cursor.execute("SELECT jwt_token FROM teacher_login WHERE teacher_id = %s AND user_name = %s", (user_id, user_name))
            result = cursor.fetchone()

            if result and result[0] == token:
                token_valid = True
                logging.info(f"Teacher token is valid for user ID: {user_id}")
            else:
                logging.warning(f"Invalid or expired teacher token for user ID: {user_id}")
        elif user_type == 'student':
           
            cursor.execute("SELECT jwt_token FROM student_login WHERE student_id = %s AND user_name = %s", (user_id, user_name))
            result = cursor.fetchone()

            if result and result[0] == token:
                token_valid = True
                logging.info(f"Student token is valid for user ID: {user_id}")
            else:
                logging.warning(f"Invalid or expired student token for user ID: {user_id}")
        else:
            logging.warning(f"Unknown user_type in token: {user_type} for user ID: {user_id}")
            return jsonify({'error': 'Unknown user type'}), 403

        if token_valid:
            return jsonify({'message': 'Token is valid', 'decoded_token': decoded}), 200 
        else:
            return jsonify({'error': 'Invalid or expired token'}), 403

    except jwt.ExpiredSignatureError:
        logging.warning("Token expired")
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        logging.warning("Invalid token")
        return jsonify({'error': 'Invalid token'}), 403
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        decoded, error_response, status_code = verify_jwt_token()
        if error_response:
            return error_response, status_code
        return f(decoded, *args, **kwargs)
    return decorated