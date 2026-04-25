from flask import Flask, request, redirect, session, render_template_string, jsonify, url_for
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT, password TEXT, username TEXT,
                  full_name TEXT, role TEXT, permission TEXT DEFAULT 'view')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, model_number TEXT,
                  serial_number TEXT, stock REAL, unit_type TEXT DEFAULT 'nos',
                  price REAL, brand TEXT, category TEXT, rack_number TEXT,
                  shelf_number TEXT, barcode TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, estimate_number TEXT, product_id INTEGER,
                  product_name TEXT, quantity_taken REAL, unit_type TEXT,
                  taken_by TEXT, date_taken TEXT, notes TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs
                 (id INTEGER PRIMARY KEY, user_id INTEGER, user_name TEXT,
                  action TEXT, details TEXT, ip_address TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    
    c.execute("SELECT * FROM users WHERE email=?", ('musthafa@purplerock.com',))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password, username, full_name, role, permission) VALUES (?,?,?,?,?,?)",
                  ('musthafa@purplerock.com', hash_password('Limara9*'), 'admin', 'Musthafa', 'admin', 'full'))
        
        sample_products = [
            ('Laptop Pro', 'LAP001', 'XPS-15', 'SN2024001', 10, 'nos', 4999.99, 'Dell', 'Electronics', 'A1', 'S1', 'BARCODE001'),
            ('Wireless Mouse', 'MOU001', 'MX-Master', 'SN2024002', 50, 'nos', 129.99, 'Logitech', 'Accessories', 'B2', 'S3', 'BARCODE002'),
            ('Network Cable', 'CAB001', 'CAT6', '', 100, 'meters', 5.99, 'Belkin', 'Cables', 'C1', 'S1', 'BARCODE003'),
        ]
        for p in sample_products:
            c.execute("INSERT INTO products (name, sku, model_number, serial_number, stock, unit_type, price, brand, category, rack_number, shelf_number, barcode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", p)
    
    conn.commit()
    conn.close()

init_db()

def log_activity(user_id, user_name, action, details='', ip=''):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO activity_logs (user_id, user_name, action, details, ip_address, timestamp) VALUES (?,?,?,?,?,?)",
              (user_id, user_name, action, details, ip, timestamp))
    conn.commit()
    conn.close()

# ============ TEMPLATES (Keep all your existing templates here) ============
# [PASTE ALL YOUR EXISTING TEMPLATES HERE - LOGIN_TEMPLATE, DASHBOARD_TEMPLATE, 
#  EDIT_TEMPLATE, ADD_TEMPLATE (ONCE!), MULTI_SCAN_TEMPLATE, USERS_TEMPLATE, 
#  TRANSACTIONS_TEMPLATE, BARCODE_TEMPLATE, ACTIVITY_LOGS_TEMPLATE, LOGO_SETTINGS_TEMPLATE]

# ============ ROUTES ============

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[3]
            session['full_name'] = user[4]
            session['role'] = user[5]
            session['permission'] = user[6]
            log_activity(user[0], user[3], 'LOGIN', f'User {email} logged in')
            return redirect('/dashboard')
        else:
            return render_template_string(LOGIN_TEMPLATE, error='Invalid email or password')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='logo_path'")
    result = c.fetchone()
    logo = result[0] if result else None
    conn.close()
    
    return render_template_string(LOGIN_TEMPLATE, logo=logo)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    
    c.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != ''")
    brands = [row[0] for row in c.fetchall()]
    
    c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
    categories = [row[0] for row in c.fetchall()]
    
    c.execute("SELECT COUNT(DISTINCT estimate_number) FROM transactions")
    total_transactions = c.fetchone()[0] or 0
    
    c.execute("SELECT value FROM settings WHERE key='logo_path'")
    result = c.fetchone()
    logo = result[0] if result else None
    conn.close()
    
    total_products = len(products)
    low_stock = sum(1 for p in products if p[5] < 10)
    total_value = sum((p[7] or 0) * p[5] for p in products)
    
    return render_template_string(DASHBOARD_TEMPLATE,
                                 products=products, brands=brands, categories=categories,
                                 total_products=total_products, low_stock=low_stock,
                                 total_value=f"{total_value:.2f}", total_transactions=total_transactions,
                                 username=session.get('username', 'User'),
                                 full_name=session.get('full_name', 'Admin'),
                                 permission=session.get('permission', 'view'), logo=logo)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        sku = request.form['sku']
        model_number = request.form.get('model_number', '')
        serial_number = request.form.get('serial_number', '')
        stock = float(request.form['stock'])
        unit_type = request.form['unit_type']
        price = float(request.form['price']) if request.form.get('price') else 0
        brand = request.form.get('brand', '')
        category = request.form.get('category', '')
        rack_number = request.form.get('rack_number', '')
        shelf_number = request.form.get('shelf_number', '')
        barcode = request.form.get('barcode', '')
        
        c.execute("""INSERT INTO products 
                     (name, sku, model_number, serial_number, stock, unit_type, price, brand, category, rack_number, shelf_number, barcode) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (name, sku, model_number, serial_number, stock, unit_type, price, brand, category, rack_number, shelf_number, barcode))
        conn.commit()
        log_activity(session['user_id'], session.get('username', 'User'), 'ADD_PRODUCT', f'Added product: {sku}')
        conn.close()
        return redirect('/dashboard')
    
    c.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != ''")
    brands = [row[0] for row in c.fetchall()]
    
    c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    
    return render_template_string(ADD_TEMPLATE, brands=brands, categories=categories)

@app.route('/users')
def users():
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    
    return render_template_string(USERS_TEMPLATE, users=users)

@app.route('/delete/<int:id>')
def delete_product(id):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT name FROM products WHERE id=?", (id,))
    product = c.fetchone()
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    if product:
        log_activity(session['user_id'], session.get('username', 'User'), 'DELETE_PRODUCT', f'Deleted product: {product[0]}')
    
    return redirect('/dashboard')

@app.route('/update/<int:id>/<int:stock>')
def update_stock(id, stock):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("UPDATE products SET stock=? WHERE id=?", (stock, id))
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], session.get('username', 'User'), 'UPDATE_STOCK', f'Updated stock for product ID {id} to {stock}')
    return redirect('/dashboard')

@app.route('/take/<int:id>/<int:quantity>/<path:estimate>')
def take_material(id, quantity, estimate):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    c.execute("SELECT name, stock, unit_type FROM products WHERE id=?", (id,))
    product = c.fetchone()
    
    if product and product[1] >= quantity:
        new_stock = product[1] - quantity
        c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, id))
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("""INSERT INTO transactions 
                     (estimate_number, product_id, product_name, quantity_taken, unit_type, taken_by, date_taken) 
                     VALUES (?,?,?,?,?,?,?)""",
                  (estimate, id, product[0], quantity, product[2], session.get('username', 'admin'), now))
        
        conn.commit()
        log_activity(session['user_id'], session.get('username', 'User'), 'TAKE_MATERIAL', f'Took {quantity} of {product[0]} for estimate {estimate}')
    
    conn.close()
    return redirect('/dashboard')

@app.route('/barcode-scanner')
def barcode_scanner():
    if 'user_id' not in session:
        return redirect('/')
    return render_template_string(BARCODE_TEMPLATE)

@app.route('/multi-scan')
def multi_scan():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT id, name, model_number, stock FROM products")
    products = c.fetchall()
    conn.close()
    
    return render_template_string(MULTI_SCAN_TEMPLATE, products=products)

@app.route('/delete-user/<int:id>')
def delete_user(id):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE id=?", (id,))
    user = c.fetchone()
    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    if user:
        log_activity(session['user_id'], session.get('username', 'User'), 'DELETE_USER', f'Deleted user: {user[0]}')
    
    return redirect('/users')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_activity(session['user_id'], session.get('username', 'User'), 'LOGOUT', 'User logged out')
    session.clear()
    return redirect('/')

# ============ ADDITIONAL ROUTES (Edit, Logo, Activity, API) ============
# [PASTE THE edit_product, logo_settings, remove_logo, activity_logs, 
#  add_user, save_multiple_serials, view_transactions, product_by_barcode routes here]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
