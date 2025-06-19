
from flask import Flask
app = Flask(__name__)

UPLOAD_FOLDER            =  'uploads'
ALLOWED_EXTENSIONS       =   {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE            =   16 * 1024 * 1024  # 16MB limit

app.config['UPLOAD_FOLDER']         =   UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH']    =   MAX_FILE_SIZE