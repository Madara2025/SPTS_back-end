from flask import Blueprint, request, jsonify
import pymysql
from config import get_db_connection
import hashlib
import jwt
import datetime
from dotenv import load_dotenv
import os


load_dotenv()


SECRET_KEY = os.getenv('jwt_secret_key') 

log_bp = Blueprint('login', __name__)

def hash_password(password):
            return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id,email):
            payload = {
                  'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
                  'user_id': user_id,
                  'email': email
            }
            return jwt.encode(payload, SECRET_KEY, algorithm ='HS256')

@log_bp.route('/login', methods=['POST'])
def login():
                  connection = get_db_connection()
                  if connection is None:
                        return jsonify({"error": "Databassee connection is failed"}), 500
                  
                  cursor = connection.cursor()
                  data = request.get_json()
                  email = data.get('email') # asign value from front end json object
                  password = data.get('password')
                  hashed_password = hash_password(password)

                  if not email or not password:
                        return jsonify({'message':'Email and password are required'}), 400
                  
                  try:
                        cursor.execute("SELECT * FROM login WHERE email = %s AND hashed_password = %s",(email, hashed_password))
                        user =  cursor.fetchone()
                        if user:
                              user_data = { "id": user[0],
                                                "email": user[1]}
                              token = create_token(user_data["id"], user_data["email"])
                              return jsonify({"message": "Login successful", "user": user_data, "token": token}), 200
                        else:
                              return jsonify({"error":"Invalid email or password"}), 401
                        
                  except pymysql.MySQLError as e:
                        return jsonify({"error": f"Database error: {e}"}), 500
                  
                  except Exception as e:
                              return jsonify({"error": f"Database error: {e}"}), 500
                  finally:
                        cursor.close()
                        connection.close()
                        
