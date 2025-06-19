from functools import wraps
from flask import session, redirect, url_for, flash




# ------------------------------ DECORATORS ------------------------------

ADMIN_USERNAME = 'Admin'
ADMIN_PASSWORD = 'Tomjerry@331'  



# Decorator to check if a user is logged in before accessing certain pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user or admin is logged in
        if 'user_id' not in session and 'admin' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function




def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash('Admin access required!')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function