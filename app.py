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

# ============ TEMPLATES ============

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Login - Inventory System</title>
<style>
body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.login-box { background: white; padding: 40px; border-radius: 10px; width: 350px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
.logo { font-size: 50px; margin-bottom: 10px; }
.logo-image { max-width: 150px; margin-bottom: 20px; }
input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
.error { color: red; margin-top: 10px; }
h2 { margin-bottom: 20px; color: #333; }
</style>
</head>
<body>
<div class="login-box">
{% if logo %}
<img src="{{ logo }}" class="logo-image">
{% else %}
<div class="logo">📦</div>
{% endif %}
<h2>Inventory Pro</h2>
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
<head><title>Dashboard - Inventory Pro</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; }
.sidebar { width: 260px; background: #1a1a2e; color: white; position: fixed; height: 100%; overflow-y: auto; }
.sidebar-header { padding: 20px; text-align: center; border-bottom: 1px solid #2a2a4e; }
.sidebar-header img { max-width: 150px; max-height: 60px; margin-bottom: 10px; }
.nav-item { padding: 15px 25px; cursor: pointer; transition: 0.3s; }
.nav-item:hover { background: #2a2a4e; }
.main-content { margin-left: 260px; padding: 20px; }
.header { background: white; padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
.user-info { display: flex; align-items: center; gap: 15px; }
.permission-badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; }
.permission-full { background: #c6f6d5; color: #22543d; }
.permission-view { background: #fed7d7; color: #742a2a; }
.search-section { background: white; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
.search-row { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; }
.search-row input, .search-row select { padding: 10px; border: 1px solid #ddd; border-radius: 5px; flex: 1; min-width: 150px; }
.reset-btn { background: #718096; color: white; padding: 10px 30px; border: none; border-radius: 5px; cursor: pointer; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
.stat-card { background: white; padding: 20px; border-radius: 12px; text-align: center; }
.stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
.stat-label { color: #666; margin-top: 5px; }
.table-container { background: white; border-radius: 12px; padding: 20px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
th { background: #f8f9fa; }
button { padding: 6px 12px; margin: 0 3px; border: none; border-radius: 5px; cursor: pointer; }
.btn-primary { background: #667eea; color: white; }
.btn-danger { background: #e53e3e; color: white; }
.btn-warning { background: #ed8936; color: white; }
.add-btn { background: #48bb78; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin-bottom: 20px; }
.low-stock { color: #e53e3e; font-weight: bold; }
.location-badge { background: #e2e8f0; padding: 2px 8px; border-radius: 12px; font-size: 12px; display: inline-block; }
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header">
{% if logo %}<img src="{{ logo }}" alt="Logo">{% else %}<h3>📦 Inventory Pro</h3>{% endif %}
</div>
<div class="nav-item" onclick="location.href='/dashboard'">📊 Dashboard</div>
<div class="nav-item" onclick="location.href='/add'">➕ Add Product</div>
<div class="nav-item" onclick="location.href='/transactions'">📋 Transactions</div>
<div class="nav-item" onclick="location.href='/barcode-scanner'">📷 Barcode Scanner</div>
<div class="nav-item" onclick="location.href='/multi-scan'">🔢 Multi-Serial Scan</div>
{% if session.permission == 'full' or session.role == 'admin' %}
<div class="nav-item" onclick="location.href='/users'">👥 User Management</div>
<div class="nav-item" onclick="location.href='/logo-settings'">🎨 Logo Settings</div>
{% endif %}
<div class="nav-item" onclick="location.href='/activity-logs'">📜 Activity Logs</div>
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>

<div class="main-content">
<div class="header">
<h2>Dashboard</h2>
<div class="user-info">
<span class="user-name">{{ username }}</span>
<span class="permission-badge permission-{{ 'full' if permission == 'full' else 'view' }}">{{ full_name }} ({{ permission | upper }})</span>
</div>
</div>

<div class="search-section">
<h3>🔍 Search Products</h3>
<div class="search-row">
<input type="text" id="searchProduct" placeholder="Product Name..." onkeyup="searchProducts()">
<input type="text" id="searchModel" placeholder="Model Number..." onkeyup="searchProducts()">
<select id="searchBrand" onchange="searchProducts()"><option value="">All Brands</option>{% for brand in brands %}<option value="{{ brand }}">{{ brand }}</option>{% endfor %}</select>
<select id="searchCategory" onchange="searchProducts()"><option value="">All Categories</option>{% for category in categories %}<option value="{{ category }}">{{ category }}</option>{% endfor %}</select>
<button class="reset-btn" onclick="resetSearch()">Reset</button>
</div>
</div>

<div class="stats">
<div class="stat-card"><div class="stat-number" id="totalDisplay">{{ total_products }}</div><div class="stat-label">Total Products</div></div>
<div class="stat-card"><div class="stat-number" id="lowStockDisplay">{{ low_stock }}</div><div class="stat-label">Low Stock</div></div>
<div class="stat-card"><div class="stat-number">AED {{ total_value }}</div><div class="stat-label">Inventory Value</div></div>
<div class="stat-card"><div class="stat-number">{{ total_transactions }}</div><div class="stat-label">Transactions</div></div>
</div>

{% if permission == 'full' or session.role == 'admin' %}<button class="add-btn" onclick="location.href='/add'">+ Add New Product</button>{% endif %}

<div class="table-container">
<h3>Product Inventory</h3>
<table id="inventoryTable"><thead><th>Name</th><th>Model #</th><th>Stock Qty</th><th>Unit</th><th>Price (AED)</th><th>Location</th><th>Actions</th></thead>
<tbody id="tableBody">
{% for product in products %}
<tr><td>{{ product[1] }}</td><td>{{ product[3] or '-' }}</td><td class="{% if product[5] < 10 %}low-stock{% endif %}">{{ product[5] }}</td><td>{{ product[6] }}</td><td>AED {{ "%.2f"|format(product[7] or 0) }}</td><td><span class="location-badge">Rack: {{ product[9] or 'N/A' }} | Shelf: {{ product[10] or 'N/A' }}</span></td>
<td>{% if permission == 'full' or session.role == 'admin' %}<button class="btn-primary" onclick="editProduct({{ product[0] }})">✏️ Edit</button><button class="btn-primary" onclick="updateStock({{ product[0] }}, {{ product[5] }})">Update</button><button class="btn-warning" onclick="takeMaterial({{ product[0] }}, '{{ product[1] }}')">Take</button><button class="btn-danger" onclick="deleteProduct({{ product[0] }})">Delete</button>{% else %}<button disabled>View Only</button>{% endif %}</td></tr>
{% endfor %}
</tbody>
</table>
</div>
</div>

<script>
let allProducts = {{ products | tojson }};
function searchProducts() {
    let productName = document.getElementById('searchProduct').value.toLowerCase();
    let modelNum = document.getElementById('searchModel').value.toLowerCase();
    let brand = document.getElementById('searchBrand').value;
    let category = document.getElementById('searchCategory').value;
    let filtered = allProducts.filter(p => {
        let match = true;
        if(productName && !p[1].toLowerCase().includes(productName)) match = false;
        if(modelNum && !(p[3] || '').toLowerCase().includes(modelNum)) match = false;
        if(brand && p[8] !== brand) match = false;
        if(category && p[9] !== category) match = false;
        return match;
    });
    let tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    filtered.forEach(p => {
        tbody.innerHTML += `<tr><td>${p[1]}</td><td>${p[3] || '-'}</td><td class="${p[5] < 10 ? 'low-stock' : ''}">${p[5]}</td><td>${p[6]}</td><td>AED ${parseFloat(p[7] || 0).toFixed(2)}</td><td><span class="location-badge">Rack: ${p[9] || 'N/A'} | Shelf: ${p[10] || 'N/A'}</span></td><td>{% if permission == 'full' or session.role == 'admin' %}<button class="btn-primary" onclick="editProduct(${p[0]})">✏️ Edit</button><button class="btn-primary" onclick="updateStock(${p[0]}, ${p[5]})">Update</button><button class="btn-warning" onclick="takeMaterial(${p[0]}, '${p[1]}')">Take</button><button class="btn-danger" onclick="deleteProduct(${p[0]})">Delete</button>{% else %}<button disabled>View Only</button>{% endif %}</td></tr>`;
    });
    document.getElementById('totalDisplay').innerText = filtered.length;
    document.getElementById('lowStockDisplay').innerText = filtered.filter(p => p[5] < 10).length;
}
function resetSearch() { document.getElementById('searchProduct').value = ''; document.getElementById('searchModel').value = ''; document.getElementById('searchBrand').value = ''; document.getElementById('searchCategory').value = ''; searchProducts(); }
{% if permission == 'full' or session.role == 'admin' %}
function editProduct(id) { window.location.href = '/edit/' + id; }
function deleteProduct(id) { if(confirm('Delete this product?')) location.href = '/delete/' + id; }
function updateStock(id, current) { let stock = prompt('Enter new stock quantity:', current); if(stock) location.href = '/update/' + id + '/' + stock; }
function takeMaterial(id, name) { let estimate = prompt('Estimate Number:', 'EST-' + Date.now()); let quantity = prompt('Quantity:', '1'); if(estimate && quantity) location.href = '/take/' + id + '/' + quantity + '/' + encodeURIComponent(estimate); }
{% endif %}
</script>
</body>
</html>
'''

ADD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Add Product - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
.container { background: white; padding: 30px; border-radius: 12px; width: 650px; }
input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
.row { display: flex; gap: 15px; }
.row > div { flex: 1; }
button { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; }
.back { background: #718096; }
</style>
</head>
<body>
<div class="container">
<h2>➕ Add New Product</h2>
<form method="POST">
<input type="text" name="name" placeholder="Product Name (Optional)">
<input type="text" name="sku" placeholder="SKU (Required)" required>
<div class="row"><div><input type="text" name="model_number" placeholder="Model Number"></div><div><input type="text" name="serial_number" placeholder="Serial Number"></div></div>
<div class="row"><div><input type="number" step="any" name="stock" placeholder="Stock Quantity" required></div><div><select name="unit_type"><option value="nos">Numbers (Nos)</option><option value="meters">Meters</option></select></div></div>
<div class="row"><div><input type="number" step="0.01" name="price" placeholder="Price (AED) - Optional"></div><div><input type="text" name="brand" placeholder="Brand" list="brandList"></div></div>
<input type="text" name="category" placeholder="Category" list="categoryList">
<h3>📍 Storage Location</h3>
<div class="row"><div><input type="text" name="rack_number" placeholder="Rack Number"></div><div><input type="text" name="shelf_number" placeholder="Shelf Number"></div></div>
<input type="text" name="barcode" placeholder="Barcode">
<datalist id="brandList">{% for brand in brands %}<option value="{{ brand }}">{% endfor %}</datalist>
<datalist id="categoryList">{% for category in categories %}<option value="{{ category }}">{% endfor %}</datalist>
<button type="submit">💾 Save Product</button>
</form>
<button class="back" onclick="location.href='/dashboard'">← Back</button>
</div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html><head><title>Edit Product</title><style>
body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px}
.container{background:white;padding:30px;border-radius:12px;width:650px}
input,select{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
.row{display:flex;gap:15px}.row>div{flex:1}
button{width:100%;padding:12px;background:#48bb78;color:white;border:none;border-radius:5px;cursor:pointer;margin-top:10px}
.back{background:#718096}
</style></head>
<body>
<div class="container"><h2>✏️ Edit Product</h2>
<form method="POST">
<input name="name" placeholder="Product Name" value="{{ product[1] }}">
<input name="sku" placeholder="SKU" value="{{ product[2] }}">
<div class="row"><div><input name="model_number" placeholder="Model Number" value="{{ product[3] or '' }}"></div><div><input name="serial_number" placeholder="Serial Number" value="{{ product[4] or '' }}"></div></div>
<div class="row"><div><input type="number" step="any" name="stock" value="{{ product[5] }}"></div><div><select name="unit_type"><option value="nos" {% if product[6]=='nos' %}selected{% endif %}>Numbers</option><option value="meters" {% if product[6]=='meters' %}selected{% endif %}>Meters</option></select></div></div>
<div class="row"><div><input type="number" step="0.01" name="price" value="{{ product[7] or '' }}"></div><div><input name="brand" value="{{ product[8] or '' }}"></div></div>
<input name="category" value="{{ product[9] or '' }}">
<div class="row"><div><input name="rack_number" value="{{ product[10] or '' }}"></div><div><input name="shelf_number" value="{{ product[11] or '' }}"></div></div>
<input name="barcode" value="{{ product[12] or '' }}">
<button type="submit">💾 Update</button>
</form><button class="back" onclick="location.href='/dashboard'">← Back</button></div>
</body></html>
'''

# Simplified templates for other pages (add these to avoid errors)
MULTI_SCAN_TEMPLATE = '<!DOCTYPE html><html><body><h2>Multi-Scan</h2><a href="/dashboard">Back</a></body></html>'
USERS_TEMPLATE = '<!DOCTYPE html><html><body><h2>User Management</h2><a href="/dashboard">Back</a></body></html>'
TRANSACTIONS_TEMPLATE = '<!DOCTYPE html><html><body><h2>Transactions</h2><a href="/dashboard">Back</a></body></html>'
BARCODE_TEMPLATE = '<!DOCTYPE html><html><body><h2>Barcode Scanner</h2><a href="/dashboard">Back</a></body></html>'
ACTIVITY_LOGS_TEMPLATE = '<!DOCTYPE html><html><body><h2>Activity Logs</h2><a href="/dashboard">Back</a></body></html>'
LOGO_SETTINGS_TEMPLATE = '<!DOCTYPE html><html><body><h2>Logo Settings</h2><a href="/dashboard">Back</a></body></html>'

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
        return render_template_string(LOGIN_TEMPLATE, error='Invalid credentials')
    
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
    c.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand!=''")
    brands = [r[0] for r in c.fetchall()]
    c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category!=''")
    categories = [r[0] for r in c.fetchall()]
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
         username=session.get('username','User'), full_name=session.get('full_name','Admin'),
         permission=session.get('permission','view'), logo=logo)

@app.route('/add', methods=['GET','POST'])
def add_product():
    if 'user_id' not in session: return redirect('/')
    if session.get('permission')!='full' and session.get('role')!='admin': return "Access Denied",403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if request.method == 'POST':
        c.execute("INSERT INTO products (name,sku,model_number,serial_number,stock,unit_type,price,brand,category,rack_number,shelf_number,barcode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (request.form.get('name',''), request.form['sku'], request.form.get('model_number',''),
                   request.form.get('serial_number',''), float(request.form['stock']), request.form['unit_type'],
                   float(request.form['price']) if request.form.get('price') else 0, request.form.get('brand',''),
                   request.form.get('category',''), request.form.get('rack_number',''), request.form.get('shelf_number',''),
                   request.form.get('barcode','')))
        conn.commit()
        log_activity(session['user_id'], session.get('username','User'), 'ADD_PRODUCT', f'Added product: {request.form["sku"]}')
        conn.close()
        return redirect('/dashboard')
    c.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand!=''")
    brands = [r[0] for r in c.fetchall()]
    c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category!=''")
    categories = [r[0] for r in c.fetchall()]
    conn.close()
    return render_template_string(ADD_TEMPLATE, brands=brands, categories=categories)

@app.route('/users')
def users():
    if 'user_id' not in session: return redirect('/')
    if session.get('permission')!='full' and session.get('role')!='admin': return "Access Denied",403
    return render_template_string(USERS_TEMPLATE)

@app.route('/delete/<int:id>')
def delete_product(id):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission')!='full' and session.get('role')!='admin': return "Access Denied",403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/update/<int:id>/<int:stock>')
def update_stock(id, stock):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission')!='full' and session.get('role')!='admin': return "Access Denied",403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("UPDATE products SET stock=? WHERE id=?", (stock, id))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/take/<int:id>/<int:quantity>/<path:estimate>')
def take_material(id, quantity, estimate):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission')!='full' and session.get('role')!='admin': return "Access Denied",403
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

@app.route('/barcode-scanner')
def barcode_scanner(): return render_template_string(BARCODE_TEMPLATE)

@app.route('/multi-scan')
def multi_scan(): return render_template_string(MULTI_SCAN_TEMPLATE)

@app.route('/activity-logs')
def activity_logs(): return render_template_string(ACTIVITY_LOGS_TEMPLATE)

@app.route('/logo-settings', methods=['GET','POST'])
def logo_settings(): return render_template_string(LOGO_SETTINGS_TEMPLATE)

@app.route('/transactions')
def view_transactions(): return render_template_string(TRANSACTIONS_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
