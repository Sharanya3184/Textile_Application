
from flask import Flask
import os
import io
from PIL import Image



app = Flask(__name__)

UPLOAD_FOLDER            =  'uploads'
ALLOWED_EXTENSIONS       =   {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE            =   16 * 1024 * 1024  # 16MB limit

app.config['UPLOAD_FOLDER']         =   UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH']    =   MAX_FILE_SIZE



# ------------------------------ UPLOAD FOLDER INIT ------------------------------

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ------------------------------ IMAGE HELPERS ------------------------------

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_data, max_size=(800, 600), quality=85):
    """Compress image to reduce size while maintaining quality"""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # Resize image if it's too large
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save compressed image to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Error compressing image: {e}")
        return image_data
    

