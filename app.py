from flask import Flask, request, redirect, session, render_template_string, jsonify, send_file
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
from datetime import datetime
import os
import io
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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
    
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY, estimate_number TEXT, client_name TEXT,
                  product_id INTEGER, product_name TEXT, quantity_booked REAL,
                  unit_type TEXT, booked_by TEXT, date_booked TEXT, status TEXT DEFAULT 'active')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs
                 (id INTEGER PRIMARY KEY, user_id INTEGER, user_name TEXT,
                  action TEXT, details TEXT, ip_address TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    
    c.execute("SELECT * FROM users WHERE email=?", ('musthafa@purplerock.com',))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password, username, full_name, role, permission) VALUES (?,?,?,?,?,?)",
                  ('musthafa@purplerock.com', hash_password('Limara9*'), 'admin', 'Musthafa', 'admin', 'admin'))
        
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
.success { color: green; margin-top: 10px; }
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
{% if success %}<div class="success">{{ success }}</div>{% endif %}
</div>
</body>
</html>
'''

CHANGE_PASSWORD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Change Password</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.container{background:white;border-radius:12px;padding:30px;max-width:500px;margin:0 auto}
input{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
button{width:100%;padding:12px;background:#48bb78;color:white;border:none;border-radius:5px;cursor:pointer}
.error{color:red;margin-top:10px}
.success{color:green;margin-top:10px}
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header"><h3>📦 Inventory Pro</h3></div>
<div class="nav-item" onclick="location.href='/dashboard'">📊 Dashboard</div>
<div class="nav-item" onclick="location.href='/change-password'">🔐 Change Password</div>
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>
<div class="main">
<div class="container">
<h2>Change Password</h2>
<form method="POST">
<input type="password" name="current_password" placeholder="Current Password" required>
<input type="password" name="new_password" placeholder="New Password" required>
<input type="password" name="confirm_password" placeholder="Confirm New Password" required>
<button type="submit">Update Password</button>
</form>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
{% if success %}<div class="success">{{ success }}</div>{% endif %}
</div>
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
.permission-admin { background: #c6f6d5; color: #22543d; }
.permission-full { background: #c6f6d5; color: #22543d; }
.permission-view { background: #fed7d7; color: #742a2a; }
.search-section { background: white; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
.search-row { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; }
.search-row input, .search-row select { padding: 10px; border: 1px solid #ddd; border-radius: 5px; flex: 1; min-width: 150px; }
.reset-btn { background: #718096; color: white; padding: 10px 30px; border: none; border-radius: 5px; cursor: pointer; }
.stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 30px; }
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
.btn-info { background: #4299e1; color: white; }
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
<div class="nav-item" onclick="location.href='/booking'">📅 Booking Hardware</div>
<div class="nav-item" onclick="location.href='/transactions'">📋 Transactions</div>
<div class="nav-item" onclick="location.href='/barcode-scanner'">📷 Barcode Scanner</div>
<div class="nav-item" onclick="location.href='/multi-scan'">🔢 Multi-Serial Scan</div>
<div class="nav-item" onclick="location.href='/change-password'">🔐 Change Password</div>
{% if session.role == 'admin' or session.permission == 'admin' %}
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
<span class="permission-badge permission-{{ 'admin' if permission == 'admin' else 'full' if permission == 'full' else 'view' }}">{{ full_name }} ({{ permission | upper }})</span>
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
<div class="stat-card"><div class="stat-number">{{ total_bookings }}</div><div class="stat-label">Active Bookings</div></div>
</div>

<button class="add-btn" onclick="location.href='/add'">+ Add New Product</button>

<div class="table-container">
<h3>Product Inventory</h3>
<table id="inventoryTable"><thead><th>Name</th><th>Model #</th><th>Stock Qty</th><th>Booked Qty</th><th>Available Qty</th><th>Unit</th><th>Price (AED)</th><th>Location</th><th>Actions</th></thead>
<tbody id="tableBody">
{% for product in products %}
{% set booked = product_bookings.get(product[0], 0) %}
{% set available = product[5] - booked %}
<tr id="row-{{ product[0] }}">
<td>{{ product[1] }}</td>
<td>{{ product[3] or '-' }}</td>
<td class="{% if product[5] < 10 %}low-stock{% endif %}">{{ product[5] }}</td>
<td>{{ booked }}</td>
<td class="{% if available < 10 %}low-stock{% endif %}">{{ available }}</td>
<td>{{ product[6] }}</td>
<td>AED {{ "%.2f"|format(product[7] or 0) }}</td>
<td><span class="location-badge">Rack: {{ product[9] or 'N/A' }} | Shelf: {{ product[10] or 'N/A' }}</span></td>
<td>
<button class="btn-primary" onclick="editProduct({{ product[0] }})">✏️ Edit</button>
<button class="btn-primary" onclick="updateStock({{ product[0] }}, {{ product[5] }})">Update</button>
<button class="btn-warning" onclick="takeMaterial({{ product[0] }}, '{{ product[1] }}')">Take</button>
<button class="btn-info" onclick="bookProduct({{ product[0] }}, '{{ product[1] }}', {{ product[5] }}, {{ booked }})">Book</button>
<button class="btn-danger" onclick="deleteProduct({{ product[0] }})">Delete</button>
</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
</div>

<script>
let allProducts = {{ products | tojson }};
let productBookings = {{ product_bookings | tojson }};

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
        let booked = productBookings[p[0]] || 0;
        let available = p[5] - booked;
        tbody.innerHTML += `<tr>
<td>${p[1]}</td>
<td>${p[3] || '-'}</td>
<td class="${p[5] < 10 ? 'low-stock' : ''}">${p[5]}</td>
<td>${booked}</td>
<td class="${available < 10 ? 'low-stock' : ''}">${available}</td>
<td>${p[6]}</td>
<td>AED ${parseFloat(p[7] || 0).toFixed(2)}</td>
<td><span class="location-badge">Rack: ${p[9] || 'N/A'} | Shelf: ${p[10] || 'N/A'}</span></td>
<td>
<button class="btn-primary" onclick="editProduct(${p[0]})">✏️ Edit</button>
<button class="btn-primary" onclick="updateStock(${p[0]}, ${p[5]})">Update</button>
<button class="btn-warning" onclick="takeMaterial(${p[0]}, '${p[1]}')">Take</button>
<button class="btn-info" onclick="bookProduct(${p[0]}, '${p[1]}', ${p[5]}, ${booked})">Book</button>
<button class="btn-danger" onclick="deleteProduct(${p[0]})">Delete</button>
</td>
</tr>`;
    });
    document.getElementById('totalDisplay').innerText = filtered.length;
    document.getElementById('lowStockDisplay').innerText = filtered.filter(p => p[5] < 10).length;
}
function resetSearch() { document.getElementById('searchProduct').value = ''; document.getElementById('searchModel').value = ''; document.getElementById('searchBrand').value = ''; document.getElementById('searchCategory').value = ''; searchProducts(); }
function editProduct(id) { window.location.href = '/edit/' + id; }
function deleteProduct(id) { if(confirm('Delete this product?')) location.href = '/delete/' + id; }
function updateStock(id, current) { let stock = prompt('Enter new stock quantity:', current); if(stock) location.href = '/update/' + id + '/' + stock; }
function takeMaterial(id, name) { let estimate = prompt('Estimate Number:', 'EST-' + Date.now()); let quantity = prompt('Quantity:', '1'); if(estimate && quantity) location.href = '/take/' + id + '/' + quantity + '/' + encodeURIComponent(estimate); }
function bookProduct(id, name, stock, booked) {
    let available = stock - booked;
    let estimate = prompt('Estimate Number for booking:', 'BOOK-' + Date.now());
    let client = prompt('Client Name:', '');
    let quantity = prompt('Quantity to book (Available: ' + available + '):', '1');
    if(estimate && client && quantity && parseInt(quantity) <= available) {
        location.href = '/book/' + id + '/' + quantity + '/' + encodeURIComponent(estimate) + '/' + encodeURIComponent(client);
    } else if(parseInt(quantity) > available) {
        alert('Not enough stock! Available: ' + available);
    }
}
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

BOOKING_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Book Hardware - Inventory Pro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px}
.container{background:white;border-radius:12px;padding:30px;max-width:800px;margin:0 auto}
table{width:100%;border-collapse:collapse}
th,td{padding:10px;text-align:left;border-bottom:1px solid #ddd}
th{background:#f8f9fa}
.low-stock{color:#e53e3e;font-weight:bold}
button{padding:6px 12px;background:#4299e1;color:white;border:none;border-radius:5px;cursor:pointer}
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header"><h3>📦 Inventory Pro</h3></div>
<div class="nav-item" onclick="location.href='/dashboard'">📊 Dashboard</div>
<div class="nav-item" onclick="location.href='/booking'">📅 Book Hardware</div>
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>
<div class="main">
<div class="header"><h2>📅 Book Hardware</h2></div>
<div class="container">
<h3>Available Products</h3>
<table>
<thead><th>Product</th><th>Model</th><th>Available Stock</th><th>Unit</th><th>Book</th></thead>
<tbody>
{% for product in products %}
{% set booked = product_bookings.get(product[0], 0) %}
{% set available = product[5] - booked %}
<tr>
<td>{{ product[1] }}</td>
<td>{{ product[3] or '-' }}</td>
<td class="{% if available < 10 %}low-stock{% endif %}">{{ available }}</td>
<td>{{ product[6] }}</td>
<td><button onclick="quickBook({{ product[0] }}, '{{ product[1] }}', {{ available }})">Book</button></td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
</div>
<script>
function quickBook(id, name, available) {
    let estimate = prompt('Estimate Number:', 'BOOK-' + Date.now());
    let client = prompt('Client Name:', '');
    let quantity = prompt('Quantity to book (Available: ' + available + '):', '1');
    if(estimate && client && quantity && parseInt(quantity) <= available) {
        window.location.href = '/book/' + id + '/' + quantity + '/' + encodeURIComponent(estimate) + '/' + encodeURIComponent(client);
    } else if(parseInt(quantity) > available) {
        alert('Not enough stock! Available: ' + available);
    }
}
</script>
</body>
</html>
'''

TRANSACTIONS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Transactions - Inventory Pro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px;display:flex;justify-content:space-between}
table{width:100%;background:white;border-radius:10px;border-collapse:collapse}
th,td{padding:12px;text-align:left;border-bottom:1px solid #ddd}
th{background:#f8f9fa}
.search-box{padding:10px;width:300px;margin-bottom:20px;border:1px solid #ddd;border-radius:5px}
.back{background:#718096;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}
.export-buttons{display:flex;gap:10px;margin-bottom:20px}
.export-btn{padding:10px 20px;border:none;border-radius:5px;cursor:pointer}
.pdf-btn{background:#e53e3e;color:white}
.excel-btn{background:#48bb78;color:white}
.print-btn{background:#667eea;color:white}
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header"><h3>📦 Inventory Pro</h3></div>
<div class="nav-item" onclick="location.href='/dashboard'">📊 Dashboard</div>
<div class="nav-item" onclick="location.href='/add'">➕ Add Product</div>
<div class="nav-item" onclick="location.href='/booking'">📅 Booking Hardware</div>
<div class="nav-item" onclick="location.href='/transactions'">📋 Transactions</div>
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>

<div class="main">
<div class="header"><h2>📋 Transactions History</h2></div>

<div class="export-buttons">
<select id="estimateSelect" class="search-box" style="width:auto">
<option value="">All Estimates</option>
{% for est in estimates %}
<option value="{{ est }}">{{ est }}</option>
{% endfor %}
</select>
<button class="export-btn pdf-btn" onclick="exportPDF()">📄 Export PDF</button>
<button class="export-btn excel-btn" onclick="exportExcel()">📊 Export Excel</button>
<button class="export-btn print-btn" onclick="printReport()">🖨️ Print</button>
</div>

<table id="transTable">
<thead><th>Date</th><th>Estimate Number</th><th>Product</th><th>Quantity</th><th>Unit</th><th>Taken By</th></thead>
<tbody id="tableBody">
{% for t in transactions %}
<tr data-estimate="{{ t[1] }}">
<td>{{ t[7] }}</td>
<td><strong>{{ t[1] }}</strong></td>
<td>{{ t[3] }}</td>
<td>{{ t[4] }}</td>
<td>{{ t[5] }}</td>
<td>{{ t[6] }}</td>
</tr>
{% endfor %}
</tbody>
</table>
<br>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<script>
function filterByEstimate() {
    let estimate = document.getElementById('estimateSelect').value;
    let rows = document.querySelectorAll('#transTable tbody tr');
    rows.forEach(row => {
        if(estimate === '' || row.dataset.estimate === estimate) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
document.getElementById('estimateSelect').addEventListener('change', filterByEstimate);
function exportPDF() { let e = document.getElementById('estimateSelect').value; window.location.href = '/export/pdf/' + e; }
function exportExcel() { let e = document.getElementById('estimateSelect').value; window.location.href = '/export/excel/' + e; }
function printReport() { let e = document.getElementById('estimateSelect').value; window.open('/export/print/' + e, '_blank'); }
</script>
</body>
</html>
'''

USERS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>User Management - Inventory Pro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px}
table{width:100%;background:white;border-radius:10px;border-collapse:collapse}
th,td{padding:12px;text-align:left;border-bottom:1px solid #ddd}
th{background:#f8f9fa}
input,select{padding:8px;margin:5px;border:1px solid #ddd;border-radius:5px}
.btn{background:#48bb78;color:white;padding:8px 16px;border:none;border-radius:5px;cursor:pointer}
.btn-danger{background:#e53e3e}
.add-form{background:#f8f9fa;padding:20px;border-radius:8px;margin-bottom:20px}
.back{background:#718096;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;color:white}
.permission-badge{padding:4px 8px;border-radius:12px;font-size:12px}
.permission-admin{background:#c6f6d5;color:#22543d}
.permission-full{background:#c6f6d5;color:#22543d}
.permission-view{background:#fed7d7;color:#742a2a}
.form-row{display:flex;gap:10px;flex-wrap:wrap}
.form-row input,.form-row select{flex:1;min-width:150px}
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header"><h3>📦 Inventory Pro</h3></div>
<div class="nav-item" onclick="location.href='/dashboard'">📊 Dashboard</div>
<div class="nav-item" onclick="location.href='/users'">👥 User Management</div>
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>

<div class="main">
<div class="header"><h2>👥 User Management</h2></div>

<div class="add-form">
<h3>Add New User</h3>
<form method="POST" action="/add-user">
<div class="form-row">
<input type="email" name="email" placeholder="Email" required>
<input type="text" name="full_name" placeholder="Full Name" required>
<input type="text" name="username" placeholder="Username" required>
</div>
<div class="form-row">
<input type="password" name="password" placeholder="Password" required>
<select name="permission">
<option value="view">View Only</option>
<option value="full">Full Access</option>
<option value="admin">Admin</option>
</select>
<button type="submit" class="btn">Add User</button>
</div>
</form>
</div>

<h3>Existing Users</h3>
<table>
<thead><th>Email</th><th>Full Name</th><th>Username</th><th>Permission</th><th>Actions</th></thead>
<tbody>
{% for user in users %}
<tr>
<td>{{ user[1] }}</td>
<td>{{ user[4] or '-' }}</td>
<td>{{ user[3] }}</td>
<td><span class="permission-badge permission-{{ user[6] }}">{{ user[6] | upper }}</span></td>
<td>{% if user[1] != 'musthafa@purplerock.com' %}<a href="/delete-user/{{ user[0] }}" onclick="return confirm('Delete user?')" class="btn btn-danger" style="text-decoration:none;padding:4px 8px">Delete</a>{% else %}Admin{% endif %}</td>
</tr>
{% endfor %}
</tbody>
</table>
<br>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>
</body>
</html>
'''

BARCODE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Barcode Scanner</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px}
.scan-area{background:white;padding:20px;border-radius:10px;margin-bottom:20px;text-align:center}
#barcodeInput{width:100%;max-width:400px;padding:15px;font-size:18px;border:2px solid #667eea;border-radius:8px;margin:20px auto;display:block}
.result{background:#f8f9fa;padding:20px;border-radius:10px;margin-top:20px}
.product-found{background:#c6f6d5;padding:15px;border-radius:8px}
.product-notfound{background:#fed7d7;padding:15px;border-radius:8px}
.btn{background:#667eea;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}
.back{background:#718096;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;margin-top:20px}
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

<div class="main">
<div class="header"><h2>📷 Barcode Scanner</h2></div>
<div class="scan-area">
<h3>Scan Barcode</h3>
<p>Use your USB barcode scanner or type manually:</p>
<input type="text" id="barcodeInput" placeholder="Scan or type barcode here..." autofocus>
<button class="btn" onclick="searchBarcode()">🔍 Search</button>
</div>
<div id="result" class="result"></div>
<button class="back" onclick="location.href='/dashboard'">← Back</button>
</div>
<script>
document.getElementById('barcodeInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); searchBarcode(); }
});
function searchBarcode() {
    let barcode = document.getElementById('barcodeInput').value.trim();
    if (!barcode) return;
    fetch(`/api/product-by-barcode/${barcode}`)
        .then(res => res.json())
        .then(data => {
            if (data.found) {
                document.getElementById('result').innerHTML = `<div class="product-found"><h3>✅ Product Found!</h3><p>Name: ${data.name}</p><p>Model: ${data.model_number || '-'}</p><p>Stock: ${data.stock} ${data.unit_type}</p><p>Location: Rack ${data.rack_number || 'N/A'} / Shelf ${data.shelf_number || 'N/A'}</p><button class="btn" onclick="location.href='/dashboard'">Go to Dashboard</button></div>`;
            } else {
                document.getElementById('result').innerHTML = `<div class="product-notfound"><h3>❌ Product Not Found</h3><p>No product found with barcode: ${barcode}</p><button class="btn" onclick="location.href='/add'">Add New Product</button></div>`;
            }
            document.getElementById('barcodeInput').value = '';
            document.getElementById('barcodeInput').focus();
        });
}
</script>
</body>
</html>
'''

MULTI_SCAN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Multi-Serial Scanner</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px}
.scan-area{background:white;padding:20px;border-radius:10px;margin-bottom:20px}
#serialInput{width:100%;padding:15px;font-size:16px;border:2px solid #667eea;border-radius:8px}
.serial-list{background:#f8f9fa;border-radius:10px;max-height:300px;overflow-y:auto;margin:20px 0}
.serial-item{padding:10px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between}
.remove-btn{background:#e53e3e;color:white;border:none;border-radius:5px;padding:5px 10px;cursor:pointer}
select{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
.btn{padding:10px 20px;border:none;border-radius:5px;cursor:pointer;margin:5px}
.btn-success{background:#48bb78;color:white}
.btn-danger{background:#e53e3e;color:white}
.back{background:#718096;color:white}
.stats{background:#e2e8f0;padding:10px;border-radius:5px;margin:10px 0}
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
<div class="main">
<div class="header"><h2>🔢 Multi-Serial Scanner</h2></div>
<div class="scan-area">
<h3>USB Barcode Scanner Mode</h3>
<p>Scan items - each scan will be added to the list below:</p>
<input type="text" id="serialInput" placeholder="Scan or type serial number..." autofocus>
<div class="stats">📊 Scanned: <span id="count">0</span> items</div>
</div>
<select id="productSelect">
<option value="">-- Select Product --</option>
{% for p in products %}<option value="{{ p[0] }}">{{ p[1] }} - {{ p[2] or 'No Model' }} (Stock: {{ p[3] }})</option>{% endfor %}
</select>
<div id="serialList" class="serial-list"></div>
<button class="btn btn-success" onclick="saveSerials()">💾 Save All</button>
<button class="btn btn-danger" onclick="clearAll()">🗑️ Clear All</button>
<button class="btn back" onclick="location.href='/dashboard'">← Back</button>
</div>
<script>
let serials = [];
document.getElementById('serialInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        let serial = this.value.trim();
        if (serial && !serials.includes(serial)) { serials.push(serial); updateList(); this.value = ''; }
    }
});
function updateList() {
    let container = document.getElementById('serialList');
    document.getElementById('count').innerText = serials.length;
    if (serials.length === 0) { container.innerHTML = '<div style="padding:20px;text-align:center;color:#999">No serials scanned yet</div>'; return; }
    container.innerHTML = '';
    serials.forEach((s, i) => { container.innerHTML += `<div class="serial-item"><span>📦 ${s}</span><button class="remove-btn" onclick="removeSerial(${i})">Remove</button></div>`; });
}
function removeSerial(i) { serials.splice(i,1); updateList(); }
function clearAll() { if(confirm('Clear all?')) { serials = []; updateList(); } }
function saveSerials() {
    let pid = document.getElementById('productSelect').value;
    let est = prompt('Estimate Number:');
    if (!pid) { alert('Select product'); return; }
    if (!est) { alert('Enter estimate'); return; }
    if (serials.length === 0) { alert('No serials'); return; }
    fetch('/api/save-multiple-serials', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: pid, serials: serials, estimate: est})
    }).then(res => res.json()).then(data => { if(data.success) { alert('Saved!'); serials = []; updateList(); } else alert('Error'); });
}
</script>
</body>
</html>
'''

ACTIVITY_LOGS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Activity Logs</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px}
table{width:100%;background:white;border-radius:10px;border-collapse:collapse}
th,td{padding:12px;text-align:left;border-bottom:1px solid #ddd}
th{background:#f8f9fa}
.search-box{padding:10px;width:300px;margin-bottom:20px;border:1px solid #ddd;border-radius:5px}
.back{background:#718096;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}
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
<div class="main">
<div class="header"><h2>📜 Activity Logs</h2></div>
<input type="text" class="search-box" id="searchBox" placeholder="Search by user or action..." onkeyup="searchTable()">
<table id="logTable">
<thead><th>Timestamp</th><th>User</th><th>Action</th><th>Details</th></thead>
<tbody>
{% for log in logs %}
<tr><td>{{ log[6] }}</td><td><strong>{{ log[2] }}</strong></td><td>{{ log[3] }}</td><td>{{ log[4] }}</td></tr>
{% endfor %}
</tbody>
</table>
<br>
<button class="back" onclick="location.href='/dashboard'">← Back</button>
</div>
<script>function searchTable(){let i=document.getElementById('searchBox');let f=i.value.toLowerCase();let r=document.querySelectorAll('#logTable tbody tr');r.forEach(row=>{row.style.display=row.innerText.toLowerCase().includes(f)?'':'none';});}</script>
</body>
</html>
'''

LOGO_SETTINGS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Logo Settings</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial;background:#f0f2f5}
.sidebar{width:250px;background:#1a1a2e;color:white;position:fixed;height:100%}
.sidebar-header{padding:20px;text-align:center}
.nav-item{padding:15px 25px;cursor:pointer}
.nav-item:hover{background:#2a2a4e}
.main{margin-left:250px;padding:20px}
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px}
.container{background:white;padding:30px;border-radius:10px;text-align:center}
.preview{margin:20px 0;padding:20px;background:#f8f9fa;border-radius:8px}
.current-logo{max-width:200px;max-height:80px}
.btn{padding:12px 24px;border:none;border-radius:5px;cursor:pointer;margin:5px}
.btn-primary{background:#667eea;color:white}
.btn-danger{background:#e53e3e;color:white}
.back{background:#718096;color:white}
input[type="file"]{margin:20px 0}
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
<div class="main">
<div class="header"><h2>🎨 Logo Settings</h2></div>
<div class="container">
<div class="preview"><h3>Current Logo</h3>{% if logo %}<img src="{{ logo }}" class="current-logo">{% else %}<p>No logo uploaded. Using default 📦 icon.</p>{% endif %}</div>
<form method="POST" enctype="multipart/form-data"><input type="file" name="logo" accept="image/*" required><button type="submit" class="btn btn-primary">Upload Logo</button></form>
<form method="POST" action="/remove-logo" style="margin-top:20px"><button type="submit" class="btn btn-danger" onclick="return confirm('Remove logo?')">Remove Logo</button></form>
<button class="btn back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>
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
            log_activity(user[0], user[3], 'LOGIN', f'User {email} logged in')
            return redirect('/dashboard')
        return render_template_string(LOGIN_TEMPLATE, error='Invalid credentials')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='logo_path'")
    result = c.fetchone()
    logo = result[0] if result else None
    conn.close()
    return render_template_string(LOGIN_TEMPLATE, logo=logo, success=request.args.get('success'))

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        current = hash_password(request.form['current_password'])
        new = request.form['new_password']
        confirm = request.form['confirm_password']
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE id=?", (session['user_id'],))
        stored = c.fetchone()[0]
        if current != stored:
            conn.close()
            return render_template_string(CHANGE_PASSWORD_TEMPLATE, error='Current password is incorrect')
        if new != confirm:
            conn.close()
            return render_template_string(CHANGE_PASSWORD_TEMPLATE, error='New passwords do not match')
        if len(new) < 4:
            conn.close()
            return render_template_string(CHANGE_PASSWORD_TEMPLATE, error='Password must be at least 4 characters')
        c.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new), session['user_id']))
        conn.commit()
        conn.close()
        log_activity(session['user_id'], session.get('username','User'), 'CHANGE_PASSWORD', 'User changed password')
        return redirect('/?success=Password changed successfully')
    return render_template_string(CHANGE_PASSWORD_TEMPLATE)

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
    c.execute("SELECT product_id, SUM(quantity_booked) FROM bookings WHERE status='active' GROUP BY product_id")
    bookings = {row[0]: row[1] for row in c.fetchall()}
    c.execute("SELECT COUNT(*) FROM bookings WHERE status='active'")
    total_bookings = c.fetchone()[0] or 0
    c.execute("SELECT value FROM settings WHERE key='logo_path'")
    result = c.fetchone()
    logo = result[0] if result else None
    conn.close()
    total_products = len(products)
    low_stock = sum(1 for p in products if p[5] < 10)
    total_value = sum((p[7] or 0) * p[5] for p in products)
    return render_template_string(DASHBOARD_TEMPLATE,
         products=products, brands=brands, categories=categories, product_bookings=bookings,
         total_products=total_products, low_stock=low_stock, total_bookings=total_bookings,
         total_value=f"{total_value:.2f}", total_transactions=total_transactions,
         username=session.get('username','User'), full_name=session.get('full_name','Admin'),
         permission=session.get('permission','view'), logo=logo)

@app.route('/add', methods=['GET','POST'])
def add_product():
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') not in ['full', 'admin']: return "Access Denied",403
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

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') not in ['full', 'admin']: return "Access Denied",403
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
        log_activity(session['user_id'], session.get('username','User'), 'EDIT_PRODUCT', f'Edited product ID: {id}')
        conn.close()
        return redirect('/dashboard')
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()
    conn.close()
    return render_template_string(EDIT_TEMPLATE, product=product)

@app.route('/delete/<int:id>')
def delete_product(id):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') not in ['full', 'admin']: return "Access Denied",403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    log_activity(session['user_id'], session.get('username','User'), 'DELETE_PRODUCT', f'Deleted product ID: {id}')
    conn.close()
    return redirect('/dashboard')

@app.route('/update/<int:id>/<int:stock>')
def update_stock(id, stock):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') not in ['full', 'admin']: return "Access Denied",403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("UPDATE products SET stock=? WHERE id=?", (stock, id))
    conn.commit()
    log_activity(session['user_id'], session.get('username','User'), 'UPDATE_STOCK', f'Updated stock for product ID {id} to {stock}')
    conn.close()
    return redirect('/dashboard')

@app.route('/take/<int:id>/<int:quantity>/<path:estimate>')
def take_material(id, quantity, estimate):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') not in ['full', 'admin']: return "Access Denied",403
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
        log_activity(session['user_id'], session.get('username','User'), 'TAKE_MATERIAL', f'Took {quantity} of {product[0]} for estimate {estimate}')
    conn.close()
    return redirect('/dashboard')

@app.route('/booking')
def booking():
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    c.execute("SELECT product_id, SUM(quantity_booked) FROM bookings WHERE status='active' GROUP BY product_id")
    bookings = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return render_template_string(BOOKING_TEMPLATE, products=products, product_bookings=bookings)

@app.route('/book/<int:id>/<int:quantity>/<path:estimate>/<path:client>')
def book_product(id, quantity, estimate, client):
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT name, stock, unit_type FROM products WHERE id=?", (id,))
    product = c.fetchone()
    c.execute("SELECT COALESCE(SUM(quantity_booked),0) FROM bookings WHERE product_id=? AND status='active'", (id,))
    booked = c.fetchone()[0] or 0
    available = product[1] - booked
    if product and available >= quantity:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO bookings (estimate_number, client_name, product_id, product_name, quantity_booked, unit_type, booked_by, date_booked) VALUES (?,?,?,?,?,?,?,?)",
                  (estimate, client, id, product[0], quantity, product[2], session.get('username','admin'), now))
        conn.commit()
        log_activity(session['user_id'], session.get('username','User'), 'BOOK_PRODUCT', f'Booked {quantity} of {product[0]} for {client} (Est: {estimate})')
    conn.close()
    return redirect('/dashboard')

@app.route('/users')
def users():
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') != 'admin' and session.get('role') != 'admin':
        return "Access Denied - Admin only", 403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return render_template_string(USERS_TEMPLATE, users=users)

@app.route('/add-user', methods=['POST'])
def add_user():
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') != 'admin' and session.get('role') != 'admin':
        return "Access Denied - Admin only", 403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, username, full_name, password, role, permission) VALUES (?,?,?,?,?,?)",
                  (request.form['email'], request.form['username'], request.form['full_name'],
                   hash_password(request.form['password']), 'staff', request.form['permission']))
        conn.commit()
        log_activity(session['user_id'], session.get('username','User'), 'ADD_USER', f'Added user: {request.form["email"]}')
    except:
        pass
    conn.close()
    return redirect('/users')

@app.route('/delete-user/<int:id>')
def delete_user(id):
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') != 'admin' and session.get('role') != 'admin':
        return "Access Denied - Admin only", 403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    log_activity(session['user_id'], session.get('username','User'), 'DELETE_USER', f'Deleted user ID: {id}')
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
    c.execute("SELECT DISTINCT estimate_number FROM transactions")
    estimates = [row[0] for row in c.fetchall()]
    conn.close()
    return render_template_string(TRANSACTIONS_TEMPLATE, transactions=transactions, estimates=estimates)

@app.route('/export/pdf/<estimate>')
def export_pdf(estimate):
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if estimate and estimate != 'all':
        c.execute("SELECT * FROM transactions WHERE estimate_number=? ORDER BY date_taken DESC", (estimate,))
    else:
        c.execute("SELECT * FROM transactions ORDER BY date_taken DESC")
    transactions = c.fetchall()
    conn.close()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, alignment=1)
    elements.append(Paragraph(f"Transactions Report - {estimate if estimate != 'all' else 'All Estimates'}", title_style))
    elements.append(Spacer(1, 20))
    data = [['Date', 'Estimate Number', 'Product', 'Quantity', 'Unit', 'Taken By']]
    for t in transactions:
        data.append([t[7], t[1], t[3], str(t[4]), t[5], t[6]])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'transactions_{estimate}.pdf', mimetype='application/pdf')

@app.route('/export/excel/<estimate>')
def export_excel(estimate):
    if 'user_id' not in session: return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if estimate and estimate != 'all':
        c.execute("SELECT * FROM transactions WHERE estimate_number=? ORDER BY date_taken DESC", (estimate,))
    else:
        c.execute("SELECT * FROM transactions ORDER BY date_taken DESC")
    transactions = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Estimate Number', 'Product', 'Quantity', 'Unit', 'Taken By'])
    for t in transactions:
        writer.writerow([t[7], t[1], t[3], t[4], t[5], t[6]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), as_attachment=True, download_name=f'transactions_{estimate}.csv', mimetype='text/csv')

@app.route('/export/print/<estimate>')
def export_print(estimate):
    if 'user_id' not in session: return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if estimate and estimate != 'all':
        c.execute("SELECT * FROM transactions WHERE estimate_number=? ORDER BY date_taken DESC", (estimate,))
    else:
        c.execute("SELECT * FROM transactions ORDER BY date_taken DESC")
    transactions = c.fetchall()
    conn.close()
    html = f'<!DOCTYPE html><html><head><title>Transactions Report</title><style>body{{font-family:Arial;margin:20px}}h1{{color:#333;text-align:center}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background-color:#4CAF50;color:white}}tr:nth-child(even){{background-color:#f2f2f2}}@media print{{button{{display:none}}}}</style></head><body><h1>Transactions Report - {estimate if estimate != "all" else "All Estimates"}</h1><button onclick="window.print()">🖨️ Print</button><table><thead><tr><th>Date</th><th>Estimate Number</th><th>Product</th><th>Quantity</th><th>Unit</th><th>Taken By</th></tr></thead><tbody>'
    for t in transactions:
        html += f'<tr><td>{t[7]}</td><td>{t[1]}</td><td>{t[3]}</td><td>{t[4]}</td><td>{t[5]}</td><td>{t[6]}</td></tr>'
    html += '</tbody></table></body></html>'
    return render_template_string(html)

@app.route('/barcode-scanner')
def barcode_scanner():
    if 'user_id' not in session: return redirect('/')
    return render_template_string(BARCODE_TEMPLATE)

@app.route('/multi-scan')
def multi_scan():
    if 'user_id' not in session: return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT id, name, model_number, stock FROM products")
    products = c.fetchall()
    conn.close()
    return render_template_string(MULTI_SCAN_TEMPLATE, products=products)

@app.route('/activity-logs')
def activity_logs():
    if 'user_id' not in session: return redirect('/')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 500")
    logs = c.fetchall()
    conn.close()
    return render_template_string(ACTIVITY_LOGS_TEMPLATE, logs=logs)

@app.route('/logo-settings', methods=['GET', 'POST'])
def logo_settings():
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') not in ['full', 'admin']: return "Access Denied",403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if request.method == 'POST':
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename:
                filename = secure_filename(f"logo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", ('logo_path', f'/static/uploads/{filename}'))
                conn.commit()
                log_activity(session['user_id'], session.get('username','User'), 'UPLOAD_LOGO', 'Updated company logo')
    c.execute("SELECT value FROM settings WHERE key='logo_path'")
    result = c.fetchone()
    logo = result[0] if result else None
    conn.close()
    return render_template_string(LOGO_SETTINGS_TEMPLATE, logo=logo)

@app.route('/remove-logo', methods=['POST'])
def remove_logo():
    if 'user_id' not in session: return redirect('/')
    if session.get('permission') not in ['full', 'admin']: return "Access Denied",403
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM settings WHERE key='logo_path'")
    conn.commit()
    log_activity(session['user_id'], session.get('username','User'), 'REMOVE_LOGO', 'Removed company logo')
    conn.close()
    return redirect('/logo-settings')

@app.route('/logout')
def logout():
    log_activity(session.get('user_id'), session.get('username','User'), 'LOGOUT', 'User logged out')
    session.clear()
    return redirect('/')

# ============ API ROUTES ============

@app.route('/api/save-multiple-serials', methods=['POST'])
def save_multiple_serials():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.json
    product_id = data['product_id']
    serials = data['serials']
    estimate = data['estimate']
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT name, stock, unit_type FROM products WHERE id=?", (product_id,))
    product = c.fetchone()
    if product:
        new_stock = product[1] + len(serials)
        c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for serial in serials:
            c.execute("INSERT INTO transactions (estimate_number, product_id, product_name, quantity_taken, unit_type, taken_by, date_taken, notes) VALUES (?,?,?,?,?,?,?,?)",
                      (estimate, product_id, product[0], 1, product[2], session.get('username', 'admin'), now, f'Serial: {serial}'))
        conn.commit()
        log_activity(session['user_id'], session.get('username','User'), 'BULK_ADD', f'Added {len(serials)} items via scanner')
        conn.close()
        return jsonify({'success': True, 'message': f'Added {len(serials)} items'})
    conn.close()
    return jsonify({'success': False, 'message': 'Product not found'})

@app.route('/api/product-by-barcode/<barcode>')
def api_product_by_barcode(barcode):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE barcode=? OR serial_number=?", (barcode, barcode))
    product = c.fetchone()
    conn.close()
    if product:
        return jsonify({
            'found': True,
            'name': product[1],
            'model_number': product[3],
            'serial_number': product[4],
            'stock': product[5],
            'unit_type': product[6],
            'price': product[7],
            'rack_number': product[10],
            'shelf_number': product[11]
        })
    return jsonify({'found': False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
