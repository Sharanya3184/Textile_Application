# ------------------------------ IMPORTS ------------------------------

import os
import base64
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from modules import *
from config import *
from decorators import *
from functools import wraps
from PIL import Image
from bson import ObjectId
from bson.regex import Regex
from urllib.parse import unquote
from modules import products_collection, categories_collection
from init import *
from dotenv import load_dotenv
load_dotenv()



# ------------------------------ FLASK APP SETUP ------------------------------

app = Flask(__name__)
app.secret_key = 'sharanya@331'

# ------------------------------ ROUTES ------------------------------


@app.route('/')
def index():
    return render_template('index.html')



# User login route
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        
        try:
            # Find user in the database
            user = users_collection.find_one({'name': name})
            
            # Check if user exists and password is correct
            if user and check_password_hash(user['password'], password):
                session['user_id']       =  str(user['_id'])
                session['user_name']     =  user['name']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid name or password!')
        except Exception as e:
            flash(f'Login error: {str(e)}')
    
    return render_template('user_login.html')




# Admin login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if admin credentials are correct
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin']            =       True
            session['admin_name']       =       'Administrator'
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid admin credentials!')
    
    return render_template('admin_login.html')



# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name                = request.form['name']
        age                 = request.form['age']
        phone               = request.form['phone']
        address             = request.form['address']
        gender              = request.form['gender']
        password            = request.form['password']
        confirm_password    = request.form['confirm_password']
        
        try:
            # Check if passwords match
            if password != confirm_password:
                flash('Passwords do not match!')
                return render_template('register.html')
            
            # Check if user already exists
            if users_collection.find_one({'name': name}):
                flash('Name already registered!')
                return render_template('register.html')
            
            # Create new user data
            user_data = {
                'name'              : name,
                'age'               : int(age),
                'phone'             : phone,
                'address'           : address,
                'gender'            : gender,
                'password'          : generate_password_hash(password),
                'registered_at'     : datetime.now()
            }
            
            # Insert new user into the database
            users_collection.insert_one(user_data)
            flash('Registration successful! Please login.')
            return redirect(url_for('user_login'))
        except Exception as e:
            flash(f'Registration error: {str(e)}')
    
    return render_template('register.html')




# Dashboard route (shows recent offers and categories)
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get the "Offer Products" category
        offer_category = categories_collection.find_one({'name': 'Offer Products'})
        recent_offers = []


        
        # Get recent products in "Offer Products" category
        if offer_category:
            recent_offers = list(products_collection.find(
                {'category': 'Offer Products'}
            ).sort('upload_date', -1).limit(5))


        
        # Get all categories for dropdown
        categories = list(categories_collection.find())
        
        # Check if admin is logged in
        is_admin  = 'admin' in session
        user_name = session.get('admin_name', session.get('user_name', 'User'))
        
        return render_template('dashboard.html', 
                             recent_offers  =   recent_offers, 
                             categories     =   categories,
                             is_admin       =   is_admin,
                             user_name      =   user_name)
    except Exception as e:
        flash(f'Dashboard error: {str(e)}')
        return render_template('dashboard.html', 
                             recent_offers  =   [], 
                             categories     =   [],
                             is_admin       =   False,
                             user_name      =   'User')
    


# View products in a specific category
@app.route('/category/<category_name>')
@login_required
def view_category(category_name):
    try:
        category_name_decoded = unquote(category_name)
        products = list(products_collection.find({'category': category_name_decoded}))
        return render_template('category.html', products=products, 
                                                category_name=category_name_decoded)
    except Exception as e:
        flash(f'Error loading category: {str(e)}')
        return render_template('category.html', products=[], category_name=category_name)
    



# Admin: Add a new category
@app.route('/admin/add_category', methods=['GET', 'POST'])
@admin_required
def add_category():
    if request.method == 'POST':
        category_name = request.form['category_name']
        
        try:
            # Check if category already exists
            if categories_collection.find_one({'name': category_name}):
                flash('Category already exists!')
            else:
                categories_collection.insert_one({
                    'name'          : category_name,
                    'created_at'    : datetime.now()
                })
                flash('Category added successfully!')
        except Exception as e:
            flash(f'Error adding category: {str(e)}')
        
        return redirect(url_for('add_category'))
    
    try:
        categories = list(categories_collection.find())
    except Exception as e:
        flash(f'Error loading categories: {str(e)}')
        categories = []
    
    return render_template('add_category.html', categories=categories)




# Admin: Add a new product with image upload
@app.route('/admin/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        try:
            # Get form data
            product_name    = request.form['product_name']
            price           = float(request.form['price'])
            category        = request.form['category']
            
            # Handle image upload
            image_data          = None
            image_filename      = None
            
            if 'product_image' in request.files:
                file = request.files['product_image']
                
                if file and file.filename != '' and allowed_file(file.filename):
                    # Secure the filename
                    filename = secure_filename(file.filename)
                    
                    # Read image data
                    file_data = file.read()
                    
                    # Compress image
                    compressed_data = compress_image(file_data)
                    
                    # Convert to base64 for MongoDB storage
                    image_data = base64.b64encode(compressed_data).decode('utf-8')
                    image_filename = filename
                    
                    # Also save to filesystem as backup
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    with open(file_path, 'wb') as f:
                        f.write(compressed_data)
                
                elif file and file.filename != '' and not allowed_file(file.filename):
                    flash('Invalid file type! Please upload PNG, JPG, JPEG, GIF, or WEBP files only.')
                    categories = list(categories_collection.find())
                    return render_template('add_product.html', categories=categories)
            


            # Create product data
            product_data = {
                'name'          : product_name,
                'price'         : price,
                'category'      : category,
                'upload_date'   : datetime.now(),
                'uploaded_by'   : session.get('admin_name', 'Admin'),
                'image_data'    : image_data,  # Base64 encoded image
                'image_filename': image_filename,
                'has_image'     : image_data is not None
            }
            

            
            # Insert product into database
            result = products_collection.insert_one(product_data)
            
            if result.inserted_id:
                flash('Product added successfully!')
            else:
                flash('Failed to add product. Please try again.')
                
        except ValueError:
            flash('Invalid price format!')
        except Exception as e:
            flash(f'Error adding product: {str(e)}')
        
        return redirect(url_for('add_product'))
    
    try:
        categories = list(categories_collection.find())
    except Exception as e:
        flash(f'Error loading categories: {str(e)}')
        categories = []
    
    return render_template('add_product.html', categories=categories)



# Route to serve product images
@app.route('/product_image/<product_id>')
@login_required
def get_product_image(product_id):
    try:
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        
        if product and product.get('image_data'):
            # Decode base64 image data
            image_data = base64.b64decode(product['image_data'])
            
            # Return image with appropriate headers
            from flask import Response
            return Response(
                image_data,
                mimetype='image/jpeg',
                headers={
                    'Content-Disposition': f'inline; filename="{product.get("image_filename", "image.jpg")}"',
                    'Cache-Control': 'public, max-age=3600'
                }
            )
        else:
            # Return a default placeholder image or 404
            return "Image not found", 404
            
    except Exception as e:
        return f"Error loading image: {str(e)}", 500



# Admin: Delete product
@app.route('/admin/delete_product/<product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    try:
        # Find the product first to get image info
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        
        if product:
            # Delete from database
            result = products_collection.delete_one({'_id': ObjectId(product_id)})
            
            if result.deleted_count > 0:
                # Also try to delete image file from filesystem if it exists
                if product.get('image_filename'):
                    try:
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image_filename'])
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Warning: Could not delete image file: {e}")
                
                flash(f'Product "{product["name"]}" deleted successfully!')
            else:
                flash('Failed to delete product!')
        else:
            flash('Product not found!')
            
    except Exception as e:
        flash(f'Error deleting product: {str(e)}')
    
    return redirect(request.referrer or url_for('dashboard'))



# Admin: View all products for management
@app.route('/Admin/Manage_Products', methods=['GET', 'POST'])
@admin_required
def manage_products():
    try:
        # Get all products with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        # Get total count
        total_products = products_collection.count_documents({})
        
        # Get products for current page
        products = list(products_collection.find()
                       .sort('upload_date', -1)
                       .skip((page - 1) * per_page)
                       .limit(per_page))
        
        # Calculate pagination info
        total_pages = (total_products + per_page - 1) // per_page
        
        return render_template('manage_products.html',
                             products       =   products,
                             current_page   =   page,
                             total_pages    =   total_pages,
                             total_products =   total_products)
    except Exception as e:
        flash(f'Error loading products: {str(e)}')
        return render_template('manage_products.html', 
                             products       =   [],
                             current_page   =   1,
                             total_pages    =   0,
                             total_products =   0)
    
    # User: Add product to wishlist

@app.route('/Wishcart/<product_id>', methods=[' GET','POST'])
@login_required
def add_to_wishcart(product_id):
    if 'user_id' not in session:
        flash('Please login to add items to your wishlist!')
        return redirect(url_for('user_login'))
        
    user_id = session.get('user_id')
    existing = wishcart_collection.find_one({
        'user_id'       : ObjectId(user_id),
        'product_id'    : ObjectId(product_id)
    })
    
    if not existing:
        wishcart_collection.insert_one({
            'user_id'       : ObjectId(user_id),
            'product_id'    : ObjectId(product_id),
            'added_at'      : datetime.now()
        })
        flash('Product added to Wishlist!')
    else:
        flash('Product already in Wishlist!')
    return redirect(url_for('dashboard'))



@app.route('/Wishcart')
@login_required
def view_wishcart():
    if 'user_id' not in session:
        flash('Please login to view your wishlist!')
        return redirect(url_for('user_login'))
        
    user_id = session.get('user_id')
    wish_items = list(wishcart_collection.find({'user_id': ObjectId(user_id)}))
    product_ids = [item['product_id'] for item in wish_items]
    products = list(products_collection.find({'_id': {'$in': product_ids}}))
    return render_template('Wishcart.html', product_ids=product_ids,
                                            wish_items=wish_items, 
                                            products=products)



@app.route('/remove_from_wishcart/<product_id>', methods=['POST'])
@login_required
def remove_from_wishcart(product_id):
    if 'user_id' not in session:
        flash('Please login to manage your wishlist!')
        return redirect(url_for('user_login'))
        
    user_id = session.get('user_id')
    wishcart_collection.delete_one({
        'user_id'       : ObjectId(user_id),
        'product_id'    : ObjectId(product_id)
    })
    flash('Product removed from Wishlist.')
    return redirect(url_for('view_wishcart'))



@app.route('/search_products', methods=['GET'])
@login_required
def search_products():
    try:
        # Get search parameters
        product_name = request.args.get('product_name', '').strip()
        category = request.args.get('category', '').strip()
        
        # Build search query
        search_query = {}
        
        if product_name:
            # Case-insensitive search for product name
            search_query['name'] = {'$regex': f'.*{product_name}.*', '$options': 'i'}
        
        if category:
            # Exact match for category
            search_query['category'] = category
        
        # Get all categories for the search form
        categories = list(categories_collection.find())
        
        # Search products
        products = list(products_collection.find(search_query).sort('upload_date', -1))
        
        return render_template('search_results.html',
                             products=products,
                             categories=categories,
                             search_name=product_name,
                             search_category=category)
                             
    except Exception as e:
        flash(f'Error searching products: {str(e)}')
        return render_template('search_results.html',
                             products=[],
                             categories=[],
                             search_name='',
                             search_category='')



# Logout route (clears the session)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Run the app if this file is executed directly
if __name__ == '__main__':
    app.run(debug=True)