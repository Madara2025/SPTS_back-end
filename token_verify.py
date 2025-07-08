from flask import Blueprint, jsonify, request
from config import get_db_connection
import jwt
import logging
from dotenv import load_dotenv
import os
from functools import wraps

load_dotenv()
Secret_Key = os.getenv('token_secret') 

token = Blueprint('jwt_verify',__name__)

@token.route('/verify-token', methods=['GET'])
def jwt_verify():
    token = request.headers.get('Authenication')
    if not token:
        logging.warning("Missing token in request headers")
        return None, jsonify({'error': 'Missing token'}), 401
    
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        decoded = jwt.decode(token,Secret_Key,algorithms=['HS256'])
        user_id = decoded['user_id']
        user_name = decoded['user_name']
        logging.info(f"Token decoded for uder ID: {user_id} and user name: {user_name}")

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT token FROM teacher_login WHERE teacher_id = %s AND user_name = %s", (user_id, user_name))
        result = cursor.fetchone()

        if result and result[0] == token:
            logging.info(f"Token is valid for user ID: {user_id}")
            return decoded, None, None
        else:
            logging.warning(f"Invalid or expired token for user ID: {user_id}")
            return None, jsonify({'error': 'Invalid or expired token'}), 403

    except jwt.ExpiredSignatureError:
        logging.warning("Token expired")
        return jsonify({'error': 'Token expired'}), 401
    
    except jwt.ExpiredSignatureError:
        logging.warning("Token invalid")
        return jsonify({'error': 'Token invalid'}), 403
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



def required_jwt(f):
    @wraps(f)
    def deco(*args, **kwargs):
        decoded, error_response, status_code = jwt_verify()
        if error_response:
            return error_response, status_code
        return f(decoded, *args, **kwargs)
    return deco
    
