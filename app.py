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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Create upload folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize database
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Create users table with full_name
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, 
                  email TEXT, 
                  password TEXT, 
                  username TEXT,
                  full_name TEXT,
                  role TEXT,
                  permission TEXT DEFAULT 'view')''')
    
    # Create products table with unit_type
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, 
                  name TEXT, 
                  sku TEXT, 
                  model_number TEXT,
                  serial_number TEXT,
                  stock REAL, 
                  unit_type TEXT DEFAULT 'nos',
                  price REAL, 
                  brand TEXT, 
                  category TEXT,
                  rack_number TEXT,
                  shelf_number TEXT,
                  barcode TEXT)''')
    
    # Create transactions table grouped by estimate
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY,
                  estimate_number TEXT,
                  product_id INTEGER,
                  product_name TEXT,
                  quantity_taken REAL,
                  unit_type TEXT,
                  taken_by TEXT,
                  date_taken TEXT,
                  notes TEXT)''')
    
    # Create activity_logs table
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  user_name TEXT,
                  action TEXT,
                  details TEXT,
                  ip_address TEXT,
                  timestamp TEXT)''')
    
    # Create settings table for logo and other settings
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT)''')
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE email=?", ('musthafa@purplerock.com',))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password, username, full_name, role, permission) VALUES (?,?,?,?,?,?)",
                  ('musthafa@purplerock.com', hash_password('Limara9*'), 'admin', 'Musthafa', 'admin', 'full'))
        
        # Add sample products with unit_type
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

# Helper function to log activities
def log_activity(user_id, user_name, action, details='', ip=''):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO activity_logs (user_id, user_name, action, details, ip_address, timestamp) VALUES (?,?,?,?,?,?)",
              (user_id, user_name, action, details, ip, timestamp))
    conn.commit()
    conn.close()

# HTML Templates
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
.sidebar-header h3 { font-size: 18px; }
.nav-item { padding: 15px 25px; cursor: pointer; transition: 0.3s; }
.nav-item:hover { background: #2a2a4e; }
.main-content { margin-left: 260px; padding: 20px; }
.header { background: white; padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
.user-info { display: flex; align-items: center; gap: 15px; }
.user-name { font-weight: bold; color: #667eea; }
.permission-badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; }
.permission-full { background: #c6f6d5; color: #22543d; }
.permission-view { background: #fed7d7; color: #742a2a; }
.search-section { background: white; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
.search-row { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; }
.search-row input, .search-row select { padding: 10px; border: 1px solid #ddd; border-radius: 5px; flex: 1; min-width: 150px; }
.search-btn { background: #667eea; color: white; padding: 10px 30px; border: none; border-radius: 5px; cursor: pointer; }
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
.btn-success { background: #48bb78; color: white; }
.btn-warning { background: #ed8936; color: white; }
.add-btn { background: #48bb78; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin-bottom: 20px; }
.low-stock { color: #e53e3e; font-weight: bold; }
.location-badge { background: #e2e8f0; padding: 2px 8px; border-radius: 12px; font-size: 12px; display: inline-block; }
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header">
{% if logo %}
<img src="{{ logo }}" alt="Logo">
{% else %}
<h3>📦 Inventory Pro</h3>
{% endif %}
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

<!-- Advanced Search Section -->
<div class="search-section">
<h3>🔍 Search Products</h3>
<div class="search-row">
<input type="text" id="searchProduct" placeholder="Product Name..." onkeyup="searchProducts()">
<input type="text" id="searchModel" placeholder="Model Number..." onkeyup="searchProducts()">
<select id="searchBrand" onchange="searchProducts()">
    <option value="">All Brands</option>
    {% for brand in brands %}
    <option value="{{ brand }}">{{ brand }}</option>
    {% endfor %}
</select>
<select id="searchCategory" onchange="searchProducts()">
    <option value="">All Categories</option>
    {% for category in categories %}
    <option value="{{ category }}">{{ category }}</option>
    {% endfor %}
</select>
<button class="reset-btn" onclick="resetSearch()">Reset</button>
</div>
</div>

<div class="stats">
<div class="stat-card"><div class="stat-number" id="totalDisplay">{{ total_products }}</div><div class="stat-label">Total Products</div></div>
<div class="stat-card"><div class="stat-number" id="lowStockDisplay">{{ low_stock }}</div><div class="stat-label">Low Stock</div></div>
<div class="stat-card"><div class="stat-number">AED {{ total_value }}</div><div class="stat-label">Inventory Value</div></div>
<div class="stat-card"><div class="stat-number">{{ total_transactions }}</div><div class="stat-label">Transactions</div></div>
</div>

{% if permission == 'full' or session.role == 'admin' %}
<button class="add-btn" onclick="location.href='/add'">+ Add New Product</button>
{% endif %}

<div class="table-container">
<h3>Product Inventory</h3>
<div id="productsTable">
<table id="inventoryTable">
<thead>
<th>Name</th><th>Model #</th><th>Stock Qty</th><th>Unit</th><th>Price (AED)</th><th>Location</th><th>Actions</th>
</thead>
<tbody id="tableBody">
{% for product in products %}
<tr id="row-{{ product[0] }}">
<td>{{ product[1] }}</td>
<td>{{ product[3] or '-' }}</td>
<td class="{% if product[5] < 10 %}low-stock{% endif %}">{{ product[5] }}</td>
<td>{{ product[6] }}</td>
<td>AED {{ "%.2f"|format(product[7] or 0) }}</td>
<td><span class="location-badge">Rack: {{ product[9] or 'N/A' }} | Shelf: {{ product[10] or 'N/A' }}</span></td>
<td>
{% if permission == 'full' or session.role == 'admin' %}
<button class="btn-primary" onclick="editProduct({{ product[0] }})">✏️ Edit</button>
<button class="btn-primary" onclick="updateStock({{ product[0] }}, {{ product[5] }})">Update Stock</button>
<button class="btn-warning" onclick="takeMaterial({{ product[0] }}, '{{ product[1] }}')">Take</button>
<button class="btn-danger" onclick="deleteProduct({{ product[0] }})">Delete</button>
{% else %}
<button class="btn-primary" disabled style="opacity:0.5">View Only</button>
{% endif %}
</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
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
        let row = `<tr>
            <td>${p[1]}</td>
            <td>${p[3] || '-'}</td>
            <td class="${p[5] < 10 ? 'low-stock' : ''}">${p[5]}</td>
            <td>${p[6]}</td>
            <td>AED ${parseFloat(p[7] || 0).toFixed(2)}</td>
            <td><span class="location-badge">Rack: ${p[9] || 'N/A'} | Shelf: ${p[10] || 'N/A'}</span></td>
            <td>
                {% if permission == 'full' or session.role == 'admin' %}
                <button class="btn-primary" onclick="editProduct(${p[0]})">✏️ Edit</button>
                <button class="btn-primary" onclick="updateStock(${p[0]}, ${p[5]})">Update Stock</button>
                <button class="btn-warning" onclick="takeMaterial(${p[0]}, '${p[1]}')">Take</button>
                <button class="btn-danger" onclick="deleteProduct(${p[0]})">Delete</button>
                {% else %}
                <button class="btn-primary" disabled style="opacity:0.5">View Only</button>
                {% endif %}
            </td>
        </tr>`;
        tbody.innerHTML += row;
    });
    
    document.getElementById('totalDisplay').innerText = filtered.length;
    let lowStockCount = filtered.filter(p => p[5] < 10).length;
    document.getElementById('lowStockDisplay').innerText = lowStockCount;
}

function resetSearch() {
    document.getElementById('searchProduct').value = '';
    document.getElementById('searchModel').value = '';
    document.getElementById('searchBrand').value = '';
    document.getElementById('searchCategory').value = '';
    searchProducts();
}

{% if permission == 'full' or session.role == 'admin' %}
function editProduct(id) {
    window.location.href = '/edit/' + id;
}
function deleteProduct(id) {
    if(confirm('Delete this product?')) location.href = '/delete/' + id;
}
function updateStock(id, current) {
    let stock = prompt('Enter new stock quantity:', current);
    if(stock) location.href = '/update/' + id + '/' + stock;
}
function takeMaterial(id, name) {
    let estimate = prompt('Enter Estimate/Reference Number:', 'EST-' + Date.now());
    let quantity = prompt('How many ' + name + '(s) are you taking?', '1');
    if(estimate && quantity) {
        location.href = '/take/' + id + '/' + quantity + '/' + encodeURIComponent(estimate);
    }
}
{% endif %}
</script>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Edit Product - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
.container { background: white; padding: 30px; border-radius: 12px; width: 650px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
.row { display: flex; gap: 15px; }
.row > div { flex: 1; }
button { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; font-size: 16px; }
.back { background: #718096; }
h2 { margin-bottom: 20px; color: #333; }
label { font-weight: bold; margin-top: 10px; display: block; }
</style>
</head>
<body>
<div class="container">
<h2>✏️ Edit Product</h2>
<form method="POST">
<input type="text" name="name" placeholder="Product Name" value="{{ product[1] }}">
<input type="text" name="sku" placeholder="SKU" value="{{ product[2] }}">

<div class="row">
<div><input type="text" name="model_number" placeholder="Model Number" value="{{ product[3] or '' }}"></div>
<div><input type="text" name="serial_number" placeholder="Serial Number" value="{{ product[4] or '' }}"></div>
</div>

<div class="row">
<div><input type="number" step="any" name="stock" placeholder="Stock Quantity" value="{{ product[5] }}"></div>
<div>
<select name="unit_type">
<option value="nos" {% if product[6] == 'nos' %}selected{% endif %}>Numbers (Nos)</option>
<option value="meters" {% if product[6] == 'meters' %}selected{% endif %}>Meters</option>
</select>
</div>
</div>

<div class="row">
<div><input type="number" step="0.01" name="price" placeholder="Price (AED)" value="{{ product[7] or '' }}"></div>
<div><input type="text" name="brand" placeholder="Brand" value="{{ product[8] or '' }}"></div>
</div>

<div class="row">
<div><input type="text" name="category" placeholder="Category" value="{{ product[9] or '' }}"></div>
<div></div>
</div>

<h3>📍 Storage Location</h3>
<div class="row">
<div><input type="text" name="rack_number" placeholder="Rack Number" value="{{ product[10] or '' }}"></div>
<div><input type="text" name="shelf_number" placeholder="Shelf Number" value="{{ product[11] or '' }}"></div>
</div>

<input type="text" name="barcode" placeholder="Barcode" value="{{ product[12] or '' }}">

<button type="submit">💾 Update Product</button>
</form>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>
</body>
</html>
'''

ADD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Add Product - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
.container { background: white; padding: 30px; border-radius: 12px; width: 650px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
.row { display: flex; gap: 15px; }
.row > div { flex: 1; }
button { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; font-size: 16px; }
.back { background: #718096; }
h2 { margin-bottom: 20px; color: #333; }
label { font-weight: bold; margin-top: 10px; display: block; }
.optional { font-size: 12px; color: #999; font-weight: normal; }
</style>
</head>
<body>
<div class="container">
<h2>➕ Add New Product</h2>
<form method="POST">
<input type="text" name="name" placeholder="Product Name (Optional)">
<input type="text" name="sku" placeholder="SKU (Required)" required>

<div class="row">
<div><input type="text" name="model_number" placeholder="Model Number"></div>
<div><input type="text" name="serial_number" id="serial_number" placeholder="Serial Number"></div>
</div>

<div class="row">
<div><input type="number" step="any" name="stock" placeholder="Stock Quantity" required></div>
<div>
<select name="unit_type">
<option value="nos">Numbers (Nos)</option>
<option value="meters">Meters</option>
</select>
</div>
</div>

<div class="row">
<div><input type="number" step="0.01" name="price" placeholder="Price (AED) - Optional"></div>
<div><input type="text" name="brand" placeholder="Brand" list="brandList"></div>
</div>

<input type="text" name="category" placeholder="Category" list="categoryList">

<h3>📍 Storage Location</h3>
<div class="row">
<div><input type="text" name="rack_number" placeholder="Rack Number"></div>
<div><input type="text" name="shelf_number" placeholder="Shelf Number"></div>
</div>

<input type="text" name="barcode" id="barcode" placeholder="Barcode">

<datalist id="brandList">
{% for brand in brands %}
<option value="{{ brand }}">
{% endfor %}
</datalist>

<datalist id="categoryList">
{% for category in categories %}
<option value="{{ category }}">
{% endfor %}
</datalist>

<button type="submit">💾 Save Product</button>
</form>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>
</body>
</html>
<div class="container">
<h2>➕ Add New Product</h2>
<form method="POST">
<input type="text" name="name" placeholder="Product Name (Optional)">
<input type="text" name="sku" placeholder="SKU (Required)" required>

<div class="row">
<div><input type="text" name="model_number" placeholder="Model Number"></div>
<div><input type="text" name="serial_number" id="serial_number" placeholder="Serial Number"></div>
</div>

<div class="row">
<div><input type="number" step="any" name="stock" placeholder="Stock Quantity" required></div>
<div>
<select name="unit_type">
<option value="nos">Numbers (Nos)</option>
<option value="meters">Meters</option>
</select>
</div>
</div>

<div class="row">
<div><input type="number" step="0.01" name="price" placeholder="Price (AED) - Optional"></div>
<div><input type="text" name="brand" placeholder="Brand" list="brandList"></div>
</div>

<input type="text" name="category" placeholder="Category" list="categoryList">

<h3>📍 Storage Location</h3>
<div class="row">
<div><input type="text" name="rack_number" placeholder="Rack Number"></div>
<div><input type="text" name="shelf_number" placeholder="Shelf Number"></div>
</div>

<input type="text" name="barcode" id="barcode" placeholder="Barcode">

<datalist id="brandList">
{% for brand in brands %}
<option value="{{ brand }}">
{% endfor %}
</datalist>

<datalist id="categoryList">
{% for category in categories %}
<option value="{{ category }}">
{% endfor %}
</datalist>

<button type="submit">💾 Save Product</button>
</form>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>
</body>
</html>
'''
MULTI_SCAN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Multi-Serial Scanner - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; margin: 0; padding: 20px; }
.container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.scan-area { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
#serialInput { width: 100%; padding: 15px; font-size: 18px; border: 2px solid #667eea; border-radius: 8px; font-family: monospace; }
.serial-list { background: white; border: 1px solid #ddd; border-radius: 8px; max-height: 300px; overflow-y: auto; margin: 20px 0; }
.serial-item { padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.serial-item:hover { background: #f0f2ff; }
.remove-btn { background: #e53e3e; color: white; border: none; border-radius: 5px; padding: 5px 10px; cursor: pointer; }
.product-select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
.btn { padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
.btn-primary { background: #667eea; color: white; }
.btn-success { background: #48bb78; color: white; }
.btn-danger { background: #e53e3e; color: white; }
.btn-back { background: #718096; color: white; }
.stats { background: #e8f5e9; padding: 10px; border-radius: 5px; margin: 10px 0; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h2>🔢 Multi-Serial Barcode Scanner</h2>
<button class="btn-back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<div class="scan-area">
<h3>📷 USB Barcode Scanner Mode</h3>
<p>Scan items with your USB barcode reader. Each scan will be added automatically.</p>
<input type="text" id="serialInput" placeholder="Scan or type serial number here..." autofocus>
<p class="stats">📊 Scanned: <span id="scanCount">0</span> items</p>
</div>

<div class="product-select">
<label>Select Product for these serials:</label>
<select id="productSelect" class="product-select">
<option value="">-- Select a product --</option>
{% for product in products %}
<option value="{{ product[0] }}">{{ product[1] }} - {{ product[2] or 'No Model' }} (Stock: {{ product[3] }})</option>
{% endfor %}
</select>
</div>

<div class="serial-list" id="serialList">
<div style="padding: 20px; text-align: center; color: #999;">No serials scanned yet. Start scanning!</div>
</div>

<div style="margin-top: 20px;">
<button class="btn btn-success" onclick="saveAllSerials()">💾 Save All (0 items)</button>
<button class="btn btn-danger" onclick="clearAll()">🗑️ Clear All</button>
</div>
</div>

<script>
let scannedSerials = [];

document.getElementById('serialInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        let serial = this.value.trim();
        if (serial && !scannedSerials.includes(serial)) {
            scannedSerials.push(serial);
            updateSerialList();
            this.value = '';
        }
    }
});

function updateSerialList() {
    let container = document.getElementById('serialList');
    let countSpan = document.getElementById('scanCount');
    countSpan.innerText = scannedSerials.length;
    
    if (scannedSerials.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No serials scanned yet. Start scanning!</div>';
        document.querySelector('.btn-success').innerHTML = '💾 Save All (0 items)';
        return;
    }
    
    container.innerHTML = '';
    scannedSerials.forEach((serial, index) => {
        let div = document.createElement('div');
        div.className = 'serial-item';
        div.innerHTML = `
            <span>📦 ${serial}</span>
            <button class="remove-btn" onclick="removeSerial(${index})">Remove</button>
        `;
        container.appendChild(div);
    });
    document.querySelector('.btn-success').innerHTML = `💾 Save All (${scannedSerials.length} items)`;
}

function removeSerial(index) {
    scannedSerials.splice(index, 1);
    updateSerialList();
}

function clearAll() {
    if(confirm('Clear all scanned serials?')) {
        scannedSerials = [];
        updateSerialList();
    }
}

function saveAllSerials() {
    let productId = document.getElementById('productSelect').value;
    let estimate = prompt('Enter Estimate/Reference Number for this batch:', 'EST-' + Date.now());
    
    if (!productId) {
        alert('Please select a product first!');
        return;
    }
    if (!estimate) {
        alert('Please enter an estimate number!');
        return;
    }
    if (scannedSerials.length === 0) {
        alert('No serials to save!');
        return;
    }
    
    fetch('/api/save-multiple-serials', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            product_id: productId,
            serials: scannedSerials,
            estimate: estimate
        })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            alert(`✅ Successfully added ${scannedSerials.length} items!`);
            scannedSerials = [];
            updateSerialList();
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    });
}
</script>
</body>
</html>
'''

USERS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>User Management - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; margin: 0; padding: 20px; }
.container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background: #f8f9fa; }
input, select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }
.btn { padding: 8px 16px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
.btn-success { background: #48bb78; color: white; }
.btn-danger { background: #e53e3e; color: white; }
.btn-primary { background: #667eea; color: white; }
.btn-back { background: #718096; color: white; }
.add-form { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
.permission-full { color: #22543d; background: #c6f6d5; padding: 2px 8px; border-radius: 12px; display: inline-block; }
.permission-view { color: #742a2a; background: #fed7d7; padding: 2px 8px; border-radius: 12px; display: inline-block; }
.form-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.form-row input, .form-row select { flex: 1; min-width: 150px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h2>👥 User Management</h2>
<button class="btn-back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

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
</select>
<button type="submit" class="btn btn-success">Add User</button>
</div>
</form>
</div>

<h3>Existing Users</h3>
<table>
<thead>
<th>Email</th><th>Full Name</th><th>Username</th><th>Role</th><th>Permission</th><th>Actions</th>
</thead>
<tbody>
{% for user in users %}
<tr>
<td>{{ user[1] }}</td>
<td>{{ user[4] or '-' }}</td>
<td>{{ user[3] }}</td>
<td>{{ user[5] }}</td>
<td><span class="permission-{{ 'full' if user[6] == 'full' else 'view' }}">{{ user[6] | upper }}</span></td>
<td>
{% if user[1] != 'musthafa@purplerock.com' %}
<a href="/delete-user/{{ user[0] }}" onclick="return confirm('Delete this user?')" class="btn btn-danger" style="text-decoration:none">Delete</a>
{% else %}
<em>Admin</em>
{% endif %}
</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
</body>
</html>
'''

TRANSACTIONS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Transactions - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; margin: 0; padding: 20px; }
.container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background: #f8f9fa; }
.btn-back { background: #718096; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
.search-box { padding: 10px; width: 300px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; }
.detail-row { background: #f8f9fa; }
.detail-row td { padding-left: 40px; font-size: 13px; }
.main-row { background: white; }
.main-row:hover { background: #f0f2ff; cursor: pointer; }
.expand-icon { font-size: 12px; margin-right: 10px; color: #667eea; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h2>📋 Material Take Transactions (Grouped by Estimate)</h2>
<button class="btn-back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<input type="text" class="search-box" id="searchInput" placeholder="Search by Estimate Number or Product..." onkeyup="searchTable()">

<table id="transactionsTable">
<thead>
<th>Date</th><th>Estimate Number</th><th>Product Names</th><th>Total Items</th><th>Taken By</th>
</thead>
<tbody id="tableBody">
{% for estimate in grouped_transactions %}
<tr class="main-row" onclick="toggleDetails('{{ estimate.estimate }}')">
<td>{{ estimate.date }}</td>
<td><strong>📄 {{ estimate.estimate }}</strong></td>
<td>{{ estimate.products | join(', ') }}</td>
<td>{{ estimate.total_quantity }}</td>
<td>{{ estimate.taken_by }}</td>
</tr>
<tr id="details-{{ estimate.estimate }}" style="display:none;" class="detail-row">
<td colspan="5">
<table style="margin: 10px; width: calc(100% - 20px);">
{% for item in estimate.items %}
<tr><td style="border:none; padding:5px;">• {{ item.product_name }}: {{ item.quantity }} {{ item.unit_type }}</td></tr>
{% endfor %}
</table>
</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

<script>
function toggleDetails(estimate) {
    let row = document.getElementById('details-' + estimate);
    if(row.style.display === 'none') {
        row.style.display = 'table-row';
    } else {
        row.style.display = 'none';
    }
}

function searchTable() {
    let input = document.getElementById('searchInput');
    let filter = input.value.toLowerCase();
    let rows = document.querySelectorAll('#transactionsTable tbody tr.main-row');
    
    rows.forEach(row => {
        let text = row.innerText.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
        let estimate = row.querySelector('strong').innerText;
        let detailRow = document.getElementById('details-' + estimate);
        if(detailRow) detailRow.style.display = 'none';
    });
}
</script>
</body>
</html>
'''
BARCODE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Barcode Scanner - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; margin: 0; padding: 20px; }
.container { max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
#video { width: 100%; max-width: 640px; border-radius: 8px; margin: 20px auto; display: block; background: #000; }
.scan-result { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px; }
.product-info { background: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 10px; }
.btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
.btn-primary { background: #667eea; color: white; }
.btn-danger { background: #e53e3e; color: white; }
.btn-back { background: #718096; color: white; }
input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h2>📷 Barcode Scanner</h2>
<button class="btn-back" onclick="location.href='/dashboard'">← Back</button>
</div>

<div style="text-align: center;">
<button class="btn btn-primary" onclick="startScanner()">▶️ Start Camera</button>
<button class="btn btn-danger" onclick="stopScanner()">⏹️ Stop Camera</button>
</div>

<video id="video" autoplay playsinline></video>

<div class="scan-result">
<h3>Manual Entry</h3>
<input type="text" id="barcodeInput" placeholder="Type or scan barcode here" autocomplete="off">
<button class="btn btn-primary" onclick="searchByBarcode()">🔍 Search</button>

<div id="productInfo"></div>
</div>
</div>

<script src="https://unpkg.com/@zxing/library@0.18.6/umd/index.min.js"></script>
<script>
let codeReader = null;

function startScanner() {
    codeReader = new ZXing.BrowserMultiFormatReader();
    codeReader.listVideoInputDevices()
        .then((videoInputDevices) => {
            if (videoInputDevices.length > 0) {
                codeReader.decodeFromVideoDevice(videoInputDevices[0].deviceId, 'video', (result, err) => {
                    if (result) {
                        document.getElementById('barcodeInput').value = result.text;
                        searchByBarcode();
                    }
                });
            }
        })
        .catch(err => {
            alert('Camera access denied.');
        });
}

function stopScanner() {
    if (codeReader) {
        codeReader.reset();
        codeReader = null;
    }
}

function searchByBarcode() {
    const barcode = document.getElementById('barcodeInput').value;
    if (!barcode) return;
    
    fetch(`/api/product-by-barcode/${barcode}`)
        .then(res => res.json())
        .then(data => {
            if (data.found) {
                document.getElementById('productInfo').innerHTML = `
                    <div class="product-info">
                        <h3>✅ Product Found!</h3>
                        <p><strong>Name:</strong> ${data.name}</p>
                        <p><strong>Model:</strong> ${data.model_number || '-'}</p>
                        <p><strong>Serial:</strong> ${data.serial_number || '-'}</p>
                        <p><strong>Stock:</strong> ${data.stock} ${data.unit_type}</p>
                        <p><strong>Location:</strong> Rack ${data.rack_number || 'N/A'} / Shelf ${data.shelf_number || 'N/A'}</p>
                        <button onclick="location.href='/dashboard'">Go to Dashboard</button>
                    </div>
                `;
            } else {
                document.getElementById('productInfo').innerHTML = `
                    <div class="product-info" style="background:#ffebee">
                        <p>❌ Product not found with barcode: ${barcode}</p>
                        <button onclick="location.href='/add'">➕ Add New Product</button>
                    </div>
                `;
            }
        });
}

document.getElementById('barcodeInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') searchByBarcode();
});
</script>
</body>
</html>
'''

ACTIVITY_LOGS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Activity Logs - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; margin: 0; padding: 20px; }
.container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background: #f8f9fa; }
.btn-back { background: #718096; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
.search-box { padding: 10px; width: 300px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; }
.filter-bar { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-bar select { padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h2>📜 Activity Logs</h2>
<button class="btn-back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<div class="filter-bar">
<input type="text" class="search-box" id="searchInput" placeholder="Search by user, action, or details..." onkeyup="searchTable()">
<select id="actionFilter" onchange="filterByAction()">
<option value="">All Actions</option>
<option value="LOGIN">Login</option>
<option value="LOGOUT">Logout</option>
<option value="ADD_PRODUCT">Add Product</option>
<option value="EDIT_PRODUCT">Edit Product</option>
<option value="DELETE_PRODUCT">Delete Product</option>
<option value="UPDATE_STOCK">Update Stock</option>
<option value="TAKE_MATERIAL">Take Material</option>
<option value="ADD_USER">Add User</option>
<option value="DELETE_USER">Delete User</option>
</select>
</div>

<table id="logsTable">
<thead>
<th>Timestamp</th><th>User</th><th>Action</th><th>Details</th><th>IP Address</th>
</thead>
<tbody>
{% for log in logs %}
<tr>
<td>{{ log[6] }}</td>
<td><strong>{{ log[2] }}</strong></td>
<td><span class="action-badge">{{ log[3] }}</span></td>
<td>{{ log[4] }}</td>
<td>{{ log[5] }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

<style>
.action-badge { background: #e2e8f0; padding: 4px 8px; border-radius: 12px; font-size: 12px; display: inline-block; }
</style>

<script>
function searchTable() {
    let input = document.getElementById('searchInput');
    let filter = input.value.toLowerCase();
    let rows = document.querySelectorAll('#logsTable tbody tr');
    
    rows.forEach(row => {
        let text = row.innerText.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

function filterByAction() {
    let action = document.getElementById('actionFilter').value;
    let rows = document.querySelectorAll('#logsTable tbody tr');
    
    rows.forEach(row => {
        let actionCell = row.cells[2].innerText;
        if(!action || actionCell === action) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
</script>
</body>
</html>
'''

LOGO_SETTINGS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Logo Settings - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; margin: 0; padding: 20px; }
.container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; text-align: center; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.preview { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
.current-logo { max-width: 200px; max-height: 80px; margin: 10px 0; }
.btn { padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
.btn-primary { background: #667eea; color: white; }
.btn-danger { background: #e53e3e; color: white; }
.btn-back { background: #718096; color: white; }
input[type="file"] { margin: 20px 0; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h2>🎨 Logo Settings</h2>
<button class="btn-back" onclick="location.href='/dashboard'">← Back</button>
</div>

<div class="preview">
<h3>Current Logo</h3>
{% if logo %}
<img src="{{ logo }}" class="current-logo">
{% else %}
<p>No logo uploaded. Using default 📦 icon.</p>
{% endif %}
</div>

<form method="POST" enctype="multipart/form-data">
<label>Upload New Logo:</label>
<input type="file" name="logo" accept="image/*" required>
<button type="submit" class="btn btn-primary">Upload Logo</button>
</form>

<form method="POST" action="/remove-logo" style="margin-top: 20px;">
<button type="submit" class="btn btn-danger" onclick="return confirm('Remove current logo?')">Remove Logo</button>
</form>

<p style="margin-top: 20px; color: #666; font-size: 12px;">Recommended: PNG or JPG, max 500KB. Size will be automatically adjusted.</p>
</div>
</body>
</html>
'''

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
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
        
        c.execute("""UPDATE products SET 
                     name=?, sku=?, model_number=?, serial_number=?, stock=?, unit_type=?, 
                     price=?, brand=?, category=?, rack_number=?, shelf_number=?, barcode=? 
                     WHERE id=?""",
                  (name, sku, model_number, serial_number, stock, unit_type, 
                   price, brand, category, rack_number, shelf_number, barcode, id))
        conn.commit()
        
        log_activity(session['user_id'], session.get('username', 'User'), 'EDIT_PRODUCT', f'Edited product: {name}')
        conn.close()
        return redirect('/dashboard')
    
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()
    conn.close()
    
    return render_template_string(EDIT_TEMPLATE, product=product)

@app.route('/logo-settings', methods=['GET', 'POST'])
def logo_settings():
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename:
                filename = secure_filename(f"logo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", 
                         ('logo_path', f'/static/uploads/{filename}'))
                conn.commit()
                log_activity(session['user_id'], session.get('username', 'User'), 'UPLOAD_LOGO', 'Updated company logo')
    
    c.execute("SELECT value FROM settings WHERE key='logo_path'")
    result = c.fetchone()
    logo = result[0] if result else None
    conn.close()
    
    return render_template_string(LOGO_SETTINGS_TEMPLATE, logo=logo)

@app.route('/remove-logo', methods=['POST'])
def remove_logo():
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM settings WHERE key='logo_path'")
    conn.commit()
    conn.close()
    
    log_activity(session['user_id'], session.get('username', 'User'), 'REMOVE_LOGO', 'Removed company logo')
    return redirect('/logo-settings')

@app.route('/activity-logs')
def activity_logs():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 500")
    logs = c.fetchall()
    conn.close()
    
    return render_template_string(ACTIVITY_LOGS_TEMPLATE, logs=logs)

@app.route('/add-user', methods=['POST'])
def add_user():
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
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
        log_activity(session['user_id'], session.get('username', 'User'), 'ADD_USER', f'Added user: {email}')
    except Exception as e:
        pass
    conn.close()
    
    return redirect('/users')

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
        
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for serial in serials:
            c.execute("""INSERT INTO transactions 
                         (estimate_number, product_id, product_name, quantity_taken, unit_type, taken_by, date_taken, notes) 
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (estimate, product_id, product[0], 1, product[2], session.get('username', 'admin'), now, f'Serial: {serial}'))
        
        conn.commit()
        log_activity(session['user_id'], session.get('username', 'User'), 'BULK_ADD', f'Added {len(serials)} items via scanner to estimate {estimate}')
        conn.close()
        return jsonify({'success': True, 'message': f'Added {len(serials)} items'})
    
    conn.close()
    return jsonify({'success': False, 'message': 'Product not found'})

@app.route('/transactions')
def view_transactions():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("""SELECT estimate_number, date_taken, taken_by, 
                        GROUP_CONCAT(product_name) as products,
                        SUM(quantity_taken) as total_quantity,
                        GROUP_CONCAT(product_name || ' (' || quantity_taken || ' ' || unit_type || ')') as details
                 FROM transactions 
                 GROUP BY estimate_number, date_taken, taken_by 
                 ORDER BY date_taken DESC""")
    rows = c.fetchall()
    
    grouped_transactions = []
    for row in rows:
        grouped_transactions.append({
            'estimate': row[0],
            'date': row[1],
            'taken_by': row[2],
            'products': row[3].split(',') if row[3] else [],
            'total_quantity': row[4],
            'items': [{'product_name': item.split('(')[0].strip(), 'quantity': item} for item in row[5].split(',')] if row[5] else []
        })
    
    conn.close()
    return render_template_string(TRANSACTIONS_TEMPLATE, grouped_transactions=grouped_transactions)

@app.route('/api/product-by-barcode/<barcode>')
def product_by_barcode(barcode):
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
