from flask import Flask
from flask_cors import CORS
from login import log_bp 
from user_management import usr 
from student_attendance import std_att
from student_marks import std_marks
from token_verify import token
from student_view import std
app = Flask(__name__)
CORS(app)

# Register Blueprints
app.register_blueprint(log_bp)
app.register_blueprint(usr)
app.register_blueprint(std_att)
app.register_blueprint(std_marks)
app.register_blueprint(token)
app.register_blueprint(std)


if __name__ == '__main__':
    app.run(debug=True) 