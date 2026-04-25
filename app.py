from flask import Flask, request, redirect, session, render_template_string, jsonify
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
from datetime import datetime
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

# ============ SIMPLE TEMPLATES (All in one) ============

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Login</title>
<style>
body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.login-box{background:white;padding:40px;border-radius:10px;width:350px;text-align:center}
input{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
button{width:100%;padding:12px;background:#667eea;color:white;border:none;border-radius:5px;cursor:pointer}
.error{color:red;margin-top:10px}
</style>
</head>
<body>
<div class="login-box">
<h2>📦 Inventory Pro</h2>
<form method="POST">
<input type="email" name="email" placeholder="Email" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
</div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center;border-bottom:1px solid #2a2a4e}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main-content{margin-left:250px;padding:20px}
.header{background:white;padding:15px 20px;border-radius:10px;margin-bottom:20px;display:flex;justify-content:space-between}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:20px}
.stat-card{background:white;padding:20px;border-radius:10px;text-align:center}
.stat-number{font-size:32px;font-weight:bold;color:#667eea}
table{width:100%;background:white;border-radius:10px;border-collapse:collapse}
th,td{padding:12px;text-align:left;border-bottom:1px solid #ddd}
th{background:#f8f9fa}
button{padding:6px 12px;margin:0 3px;border:none;border-radius:5px;cursor:pointer}
.btn-primary{background:#667eea;color:white}
.btn-danger{background:#e53e3e;color:white}
.btn-warning{background:#ed8936;color:white}
.add-btn{background:#48bb78;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;margin-bottom:20px}
.low-stock{color:#e53e3e;font-weight:bold}
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header"><h3>📦 Inventory Pro</h3></div>
<div class="nav-item" onclick="location.href='/dashboard'">📊 Dashboard</div>
<div class="nav-item" onclick="location.href='/add'">➕ Add Product</div>
<div class="nav-item" onclick="location.href='/transactions'">📋 Transactions</div>
<div class="nav-item" onclick="location.href='/users'">👥 Users</div>
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>

<div class="main-content">
<div class="header"><h2>Dashboard</h2><div>{{ full_name }} ({{ permission }})</div></div>

<div class="stats">
<div class="stat-card"><div class="stat-number">{{ total_products }}</div><div>Total Products</div></div>
<div class="stat-card"><div class="stat-number">{{ low_stock }}</div><div>Low Stock</div></div>
<div class="stat-card"><div class="stat-number">AED {{ total_value }}</div><div>Inventory Value</div></div>
<div class="stat-card"><div class="stat-number">{{ total_transactions }}</div><div>Transactions</div></div>
</div>

<button class="add-btn" onclick="location.href='/add'">+ Add Product</button>

<table>
<thead><tr><th>Name</th><th>Model</th><th>Stock</th><th>Unit</th><th>Price</th><th>Location</th><th>Actions</th></tr></thead>
<tbody>
{% for p in products %}
<tr>
<td>{{ p[1] }}</td><td>{{ p[3] or '-' }}</td>
<td class="{% if p[5] < 10 %}low-stock{% endif %}">{{ p[5] }}</td>
<td>{{ p[6] }}</td><td>AED {{ "%.2f"|format(p[7] or 0) }}</td>
<td>Rack:{{ p[9] or 'N/A' }} Shelf:{{ p[10] or 'N/A' }}</td>
<td>
<button class="btn-primary" onclick="editProduct({{ p[0] }})">Edit</button>
<button class="btn-primary" onclick="updateStock({{ p[0] }}, {{ p[5] }})">Update</button>
<button class="btn-warning" onclick="takeMaterial({{ p[0] }}, '{{ p[1] }}')">Take</button>
<button class="btn-danger" onclick="deleteProduct({{ p[0] }})">Delete</button>
</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

<script>
function editProduct(id){ window.location.href='/edit/'+id; }
function deleteProduct(id){ if(confirm('Delete?')) location.href='/delete/'+id; }
function updateStock(id,current){ let stock=prompt('New stock:',current); if(stock) location.href='/update/'+id+'/'+stock; }
function takeMaterial(id,name){ let est=prompt('Estimate number:'); let qty=prompt('Quantity:'); if(est && qty) location.href='/take/'+id+'/'+qty+'/'+est; }
</script>
</body>
</html>
'''

ADD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Add Product</title>
<style>
body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
.container{background:white;padding:30px;border-radius:10px;width:600px}
input,select{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
.row{display:flex;gap:15px}
button{width:100%;padding:12px;background:#48bb78;color:white;border:none;border-radius:5px;cursor:pointer}
.back{background:#718096;margin-top:10px}
</style>
</head>
<body>
<div class="container">
<h2>➕ Add Product</h2>
<form method="POST">
<input name="name" placeholder="Product Name">
<input name="sku" placeholder="SKU" required>
<div class="row"><div><input name="model_number" placeholder="Model"></div><div><input name="serial_number" placeholder="Serial"></div></div>
<div class="row"><div><input type="number" step="any" name="stock" placeholder="Stock" required></div><div><select name="unit_type"><option value="nos">Numbers</option><option value="meters">Meters</option></select></div></div>
<div class="row"><div><input type="number" step="0.01" name="price" placeholder="Price AED"></div><div><input name="brand" placeholder="Brand"></div></div>
<input name="category" placeholder="Category">
<h3>Location</h3>
<div class="row"><div><input name="rack_number" placeholder="Rack"></div><div><input name="shelf_number" placeholder="Shelf"></div></div>
<input name="barcode" placeholder="Barcode">
<button type="submit">Save</button>
</form>
<button class="back" onclick="location.href='/dashboard'">Back</button>
</div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Edit Product</title>
<style>
body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
.container{background:white;padding:30px;border-radius:10px;width:600px}
input,select{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
.row{display:flex;gap:15px}
button{width:100%;padding:12px;background:#48bb78;color:white;border:none;border-radius:5px;cursor:pointer}
.back{background:#718096;margin-top:10px}
</style>
</head>
<body>
<div class="container">
<h2>✏️ Edit Product</h2>
<form method="POST">
<input name="name" value="{{ product[1] }}">
<input name="sku" value="{{ product[2] }}">
<div class="row"><div><input name="model_number" value="{{ product[3] or '' }}"></div><div><input name="serial_number" value="{{ product[4] or '' }}"></div></div>
<div class="row"><div><input type="number" step="any" name="stock" value="{{ product[5] }}"></div><div><select name="unit_type"><option value="nos" {% if product[6]=='nos' %}selected{% endif %}>Numbers</option><option value="meters" {% if product[6]=='meters' %}selected{% endif %}>Meters</option></select></div></div>
<div class="row"><div><input type="number" step="0.01" name="price" value="{{ product[7] or '' }}"></div><div><input name="brand" value="{{ product[8] or '' }}"></div></div>
<input name="category" value="{{ product[9] or '' }}">
<div class="row"><div><input name="rack_number" value="{{ product[10] or '' }}"></div><div><input name="shelf_number" value="{{ product[11] or '' }}"></div></div>
<input name="barcode" value="{{ product[12] or '' }}">
<button type="submit">Update</button>
</form>
<button class="back" onclick="location.href='/dashboard'">Back</button>
</div>
</body>
</html>
'''

USERS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Users</title>
<style>
body{font-family:Arial;background:#f0f2f5;padding:20px}
.container{background:white;border-radius:10px;padding:20px;max-width:800px;margin:0 auto}
table{width:100%;border-collapse:collapse}
th,td{padding:10px;text-align:left;border-bottom:1px solid #ddd}
.add-form{background:#f8f9fa;padding:20px;border-radius:8px;margin-bottom:20px}
input,select{padding:8px;margin:5px;border:1px solid #ddd;border-radius:5px}
.btn{background:#48bb78;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer}
</style>
</head>
<body>
<div class="container">
<h2>👥 User Management</h2>
<div class="add-form">
<h3>Add User</h3>
<form method="POST" action="/add-user">
<input type="email" name="email" placeholder="Email" required>
<input type="text" name="full_name" placeholder="Full Name" required>
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<select name="permission"><option value="view">View Only</option><option value="full">Full Access</option></select>
<button type="submit" class="btn">Add User</button>
</form>
</div>
<h3>Existing Users</h3>
<table><thead><th>Email</th><th>Full Name</th><th>Permission</th><th>Actions</th></thead>
<tbody>
{% for user in users %}
<tr><td>{{ user[1] }}</td><td>{{ user[4] or '-' }}</td><td>{{ user[6] }}</td>
<td>{% if user[1] != 'musthafa@purplerock.com' %}<a href="/delete-user/{{ user[0] }}" onclick="return confirm('Delete?')">Delete</a>{% else %}Admin{% endif %}</td></tr>
{% endfor %}
</tbody>
</table>
<button onclick="location.href='/dashboard'">Back</button>
</div>
</body>
</html>
'''

TRANSACTIONS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Transactions</title>
<style>
body{font-family:Arial;background:#f0f2f5;padding:20px}
.container{background:white;border-radius:10px;padding:20px;max-width:1000px;margin:0 auto}
table{width:100%;border-collapse:collapse}
th,td{padding:10px;text-align:left;border-bottom:1px solid #ddd}
</style>
</head>
<body>
<div class="container">
<h2>📋 Transactions</h2>
<table><thead><th>Date</th><th>Estimate</th><th>Product</th><th>Quantity</th><th>Taken By</th></thead>
<tbody>
{% for t in transactions %}
<tr><td>{{ t[7] }}</td><td><strong>{{ t[1] }}</strong></td><td>{{ t[3] }}</td><td>{{ t[4] }} {{ t[5] }}</td><td>{{ t[6] }}</td></tr>
{% endfor %}
</tbody>
</table>
<button onclick="location.href='/dashboard'">Back</button>
</div>
</body>
</html>
'''

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
            return redirect('/dashboard')
        return render_template_string(LOGIN_TEMPLATE, error='Invalid credentials')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    c.execute("SELECT COUNT(DISTINCT estimate_number) FROM transactions")
    total_transactions = c.fetchone()[0] or 0
    conn.close()
    total_products = len(products)
    low_stock = sum(1 for p in products if p[5] < 10)
    total_value = sum((p[7] or 0) * p[5] for p in products)
    return render_template_string(DASHBOARD_TEMPLATE,
         products=products, total_products=total_products, low_stock=low_stock,
         total_value=f"{total_value:.2f}", total_transactions=total_transactions,
         full_name=session.get('full_name','Admin'), permission=session.get('permission','view'))

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (name,sku,model_number,serial_number,stock,unit_type,price,brand,category,rack_number,shelf_number,barcode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (request.form.get('name',''), request.form['sku'], request.form.get('model_number',''),
                   request.form.get('serial_number',''), float(request.form['stock']), request.form['unit_type'],
                   float(request.form['price']) if request.form.get('price') else 0, request.form.get('brand',''),
                   request.form.get('category',''), request.form.get('rack_number',''), request.form.get('shelf_number',''),
                   request.form.get('barcode','')))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    return render_template_string(ADD_TEMPLATE)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if request.method == 'POST':
        c.execute("UPDATE products SET name=?, sku=?, model_number=?, serial_number=?, stock=?, unit_type=?, price=?, brand=?, category=?, rack_number=?, shelf_number=?, barcode=? WHERE id=?",
                  (request.form['name'], request.form['sku'], request.form.get('model_number',''),
                   request.form.get('serial_number',''), float(request.form['stock']), request.form['unit_type'],
                   float(request.form['price']) if request.form.get('price') else 0, request.form.get('brand',''),
                   request.form.get('category',''), request.form.get('rack_number',''), request.form.get('shelf_number',''),
                   request.form.get('barcode',''), id))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()
    conn.close()
    return render_template_string(EDIT_TEMPLATE, product=product)

@app.route('/delete/<int:id>')
def delete_product(id):
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/update/<int:id>/<int:stock>')
def update_stock(id, stock):
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("UPDATE products SET stock=? WHERE id=?", (stock, id))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/take/<int:id>/<int:quantity>/<path:estimate>')
def take_material(id, quantity, estimate):
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT name, stock, unit_type FROM products WHERE id=?", (id,))
    product = c.fetchone()
    if product and product[1] >= quantity:
        c.execute("UPDATE products SET stock=? WHERE id=?", (product[1]-quantity, id))
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO transactions (estimate_number, product_id, product_name, quantity_taken, unit_type, taken_by, date_taken) VALUES (?,?,?,?,?,?,?)",
                  (estimate, id, product[0], quantity, product[2], session.get('username','admin'), now))
        conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/users')
def users():
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template_string(USERS_TEMPLATE, users=users)

@app.route('/add-user', methods=['POST'])
def add_user():
    if 'user_id' not in session:
        return redirect('/')
    email = request.form['email']
    username = request.form['username']
    full_name = request.form['full_name']
    password = hash_password(request.form['password'])
    permission = request.form['permission']
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, username, full_name, password, role, permission) VALUES (?,?,?,?,?,?)",
                  (email, username, full_name, password, 'staff', permission))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect('/users')

@app.route('/delete-user/<int:id>')
def delete_user(id):
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/users')

@app.route('/transactions')
def view_transactions():
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM transactions ORDER BY date_taken DESC")
    transactions = c.fetchall()
    conn.close()
    return render_template_string(TRANSACTIONS_TEMPLATE, transactions=transactions)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
