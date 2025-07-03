import pymysql
from dotenv import load_dotenv
import os # os is python module for iteraction

load_dotenv()
    
def get_db_connection():
    try:
        connection = pymysql.connect(host=os.getenv('host'),
                                            database=os.getenv('mysql_database'),
                                            user=os.getenv('mysql_user'),
                                                password=os.getenv('mysql_password')
                                            )
        

        print("succsess run config ")
        return connection
    except:
        print("Somthing went wrong run config")


get_db_connection()