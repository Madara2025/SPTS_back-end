from flask import Flask
from flask_cors import CORS
from login import log_bp 
from user_management import usr 
from student_attendance import std_att

app = Flask(__name__)
CORS(app)

# Register Blueprints
app.register_blueprint(log_bp)
app.register_blueprint(usr)
app.register_blueprint(std_att)


if __name__ == '__main__':
    app.run(debug=True) 