import os
import io
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from modules import * 
from config import *




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
    


# ------------------------------ INIT DEFAULT CATEGORIES ------------------------------

def init_categories():
    try:
        default_categories = [
            {'name': 'Offer Products', 'created_at': datetime.now()},
            {'name': 'Furniture', 'created_at': datetime.now()},
            {'name': 'Electronics', 'created_at': datetime.now()}
        ]


        # Check if each category exists, if not, add it
        for category in default_categories:
            if not categories_collection.find_one({'name': category['name']}):
                categories_collection.insert_one(category)
        print("Categories initialized successfully")
    except Exception as e:
        print(f"Error initializing categories: {e}")



# Call the function to initialize categories
init_categories()
