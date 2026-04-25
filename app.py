from flask import Flask, request, redirect, session, render_template_string, jsonify
import sqlite3
import hashlib
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-2024'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize database
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Create users table with permissions
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, 
                  email TEXT, 
                  password TEXT, 
                  username TEXT,
                  role TEXT,
                  permission TEXT DEFAULT 'view')''')
    
    # Create products table with all fields
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, 
                  name TEXT, 
                  sku TEXT, 
                  model_number TEXT,
                  serial_number TEXT,
                  stock INTEGER, 
                  price REAL, 
                  brand TEXT, 
                  category TEXT,
                  rack_number TEXT,
                  shelf_number TEXT,
                  barcode TEXT)''')
    
    # Create transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY,
                  product_id INTEGER,
                  product_name TEXT,
                  serial_number TEXT,
                  quantity_taken INTEGER,
                  estimate_number TEXT,
                  taken_by TEXT,
                  date_taken TEXT,
                  notes TEXT)''')
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE email=?", ('musthafa@purplerock.com',))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password, username, role, permission) VALUES (?,?,?,?,?)",
                  ('musthafa@purplerock.com', hash_password('Limara9*'), 'Admin', 'admin', 'full'))
        
        # Add sample products
        sample_products = [
            ('Laptop Pro', 'LAP001', 'XPS-15', 'SN2024001', 10, 999.99, 'Dell', 'Electronics', 'A1', 'S1', 'BARCODE001'),
            ('Wireless Mouse', 'MOU001', 'MX-Master', 'SN2024002', 50, 29.99, 'Logitech', 'Accessories', 'B2', 'S3', 'BARCODE002'),
            ('Mechanical Keyboard', 'KEY001', 'K95', 'SN2024003', 5, 89.99, 'Corsair', 'Accessories', 'A2', 'S2', 'BARCODE003'),
            ('Gaming Monitor', 'MON001', 'Odyssey G7', 'SN2024004', 8, 499.99, 'Samsung', 'Electronics', 'C1', 'S1', 'BARCODE004'),
            ('USB Hub', 'USB001', 'UH700', 'SN2024005', 25, 45.99, 'Anker', 'Accessories', 'B1', 'S4', 'BARCODE005'),
        ]
        for p in sample_products:
            c.execute("INSERT INTO products (name, sku, model_number, serial_number, stock, price, brand, category, rack_number, shelf_number, barcode) VALUES (?,?,?,?,?,?,?,?,?,?,?)", p)
    
    conn.commit()
    conn.close()

init_db()

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Login - Inventory System</title>
<style>
body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.login-box { background: white; padding: 40px; border-radius: 10px; width: 350px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
.logo { font-size: 50px; margin-bottom: 10px; }
input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
.error { color: red; margin-top: 10px; }
h2 { margin-bottom: 20px; color: #333; }
</style>
</head>
<body>
<div class="login-box">
<div class="logo">📦</div>
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
.sidebar-header { padding: 25px; text-align: center; border-bottom: 1px solid #2a2a4e; }
.nav-item { padding: 15px 25px; cursor: pointer; transition: 0.3s; }
.nav-item:hover { background: #2a2a4e; }
.main-content { margin-left: 260px; padding: 20px; }
.header { background: white; padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
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
.location-badge { background: #e2e8f0; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
.permission-badge { padding: 2px 6px; border-radius: 10px; font-size: 11px; }
.permission-full { background: #c6f6d5; color: #22543d; }
.permission-view { background: #fed7d7; color: #742a2a; }
@media (max-width: 768px) {
    .sidebar { transform: translateX(-100%); }
    .main-content { margin-left: 0; }
}
</style>
</head>
<body>
<div class="sidebar">
<div class="sidebar-header"><h3>📦 Inventory Pro</h3></div>
<div class="nav-item" onclick="location.href='/dashboard'">📊 Dashboard</div>
<div class="nav-item" onclick="location.href='/add'">➕ Add Product</div>
<div class="nav-item" onclick="location.href='/transactions'">📋 Transactions</div>
<div class="nav-item" onclick="location.href='/barcode-scanner'">📷 Barcode Scanner</div>
<div class="nav-item" onclick="location.href='/multi-scan'">🔢 Multi-Serial Scan</div>
{% if session.permission == 'full' or session.role == 'admin' %}
<div class="nav-item" onclick="location.href='/users'">👥 User Management</div>
{% endif %}
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>

<div class="main-content">
<div class="header">
<h2>Dashboard</h2>
<div>
<span>👤 {{ username }} </span>
<span class="permission-badge permission-{{ 'full' if permission == 'full' else 'view' }}">{{ permission | upper }} ACCESS</span>
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
<div class="stat-card"><div class="stat-number">${{ total_value }}</div><div class="stat-label">Inventory Value</div></div>
<div class="stat-card"><div class="stat-number">{{ total_taken }}</div><div class="stat-label">Items Taken</div></div>
</div>

{% if permission == 'full' or session.role == 'admin' %}
<button class="add-btn" onclick="location.href='/add'">+ Add New Product</button>
{% endif %}

<div class="table-container">
<h3>Product Inventory</h3>
<div id="productsTable">
<table id="inventoryTable">
<thead>
<th>Name</th><th>Model #</th><th>Serial #</th><th>Stock</th><th>Brand</th><th>Category</th><th>Location</th><th>Actions</th>
</thead>
<tbody id="tableBody">
{% for product in products %}
<tr id="row-{{ product[0] }}">
<td>{{ product[1] }}</td>
<td>{{ product[3] or '-' }}</td>
<td><small>{{ product[4] or '-' }}</small></td>
<td {% if product[5] < 10 %}class="low-stock"{% endif %}>{{ product[5] }}</td>
<td>{{ product[7] or '-' }}</td>
<td>{{ product[8] or '-' }}</td>
<td><span class="location-badge">Rack: {{ product[9] or 'N/A' }}</span></td>
<td>
{% if permission == 'full' or session.role == 'admin' %}
<button class="btn-primary" onclick="updateStock({{ product[0] }}, {{ product[5] }})">Update</button>
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
        if(brand && p[7] !== brand) match = false;
        if(category && p[8] !== category) match = false;
        return match;
    });
    
    let tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    
    filtered.forEach(p => {
        let row = `<tr>
            <td>${p[1]}</td>
            <td>${p[3] || '-'}</td>
            <td><small>${p[4] || '-'}</small></td>
            <td class="${p[5] < 10 ? 'low-stock' : ''}">${p[5]}</td>
            <td>${p[7] || '-'}</td>
            <td>${p[8] || '-'}</td>
            <td><span class="location-badge">Rack: ${p[9] || 'N/A'}</span></td>
            <td>
                ${p[5] < 10 ? '<span class="low-stock">⚠️ Low Stock</span>' : ''}
                {% if permission == 'full' or session.role == 'admin' %}
                <button class="btn-primary" onclick="updateStock(${p[0]}, ${p[5]})">Update</button>
                <button class="btn-warning" onclick="takeMaterial(${p[0]}, '${p[1]}')">Take</button>
                <button class="btn-danger" onclick="deleteProduct(${p[0]})">Delete</button>
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
function deleteProduct(id) {
    if(confirm('Delete this product?')) location.href = '/delete/' + id;
}
function updateStock(id, current) {
    let stock = prompt('Enter new stock quantity:', current);
    if(stock) location.href = '/update/' + id + '/' + stock;
}
function takeMaterial(id, name) {
    let estimate = prompt('Enter Estimate/Reference Number:', 'EST-{{ now }}');
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
.scan-btn { background: #667eea; padding: 8px 16px; font-size: 14px; width: auto; margin-left: 10px; }
.serial-row { display: flex; gap: 10px; align-items: center; }
.serial-row input { flex: 1; }
.dropdown-hint { font-size: 12px; color: #666; margin-top: -5px; margin-bottom: 5px; }
</style>
</head>
<body>
<div class="container">
<h2>➕ Add New Product</h2>
<form method="POST">
<input type="text" name="name" placeholder="Product Name" list="productList" required>
<datalist id="productList">
{% for name in product_names %}
<option value="{{ name }}">
{% endfor %}
</datalist>

<input type="text" name="sku" placeholder="SKU" required>

<div class="row">
<div>
<input type="text" name="model_number" placeholder="Model Number" list="modelList">
<datalist id="modelList">
{% for model in models %}
<option value="{{ model }}">
{% endfor %}
</datalist>
</div>
<div class="serial-row">
<input type="text" name="serial_number" id="serial_number" placeholder="Serial Number">
<button type="button" class="scan-btn" onclick="simulateScan()">📷 Scan</button>
</div>
</div>

<div class="row">
<div><input type="number" name="stock" placeholder="Stock Quantity" required></div>
<div><input type="number" step="0.01" name="price" placeholder="Price" required></div>
</div>

<div class="row">
<div>
<input type="text" name="brand" placeholder="Brand" list="brandList">
<datalist id="brandList">
{% for brand in brands %}
<option value="{{ brand }}">
{% endfor %}
</datalist>
<div class="dropdown-hint">💡 Type or select from existing brands</div>
</div>
<div>
<input type="text" name="category" placeholder="Category" list="categoryList">
<datalist id="categoryList">
{% for category in categories %}
<option value="{{ category }}">
{% endfor %}
</datalist>
<div class="dropdown-hint">💡 Type or select from existing categories</div>
</div>
</div>

<h3>📍 Storage Location</h3>
<div class="row">
<div><input type="text" name="rack_number" placeholder="Rack Number (e.g., A1, B2)"></div>
<div><input type="text" name="shelf_number" placeholder="Shelf Number (e.g., S1, S2)"></div>
</div>

<input type="text" name="barcode" id="barcode" placeholder="Barcode (optional)">

<button type="submit">💾 Save Product</button>
</form>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<script>
function simulateScan() {
    let scanned = prompt('Scan or enter barcode/serial number:', 'SN' + Date.now());
    if(scanned) {
        document.getElementById('serial_number').value = scanned;
        document.getElementById('barcode').value = scanned;
    }
}
</script>
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
<option value="{{ product[0] }}">{{ product[1] }} - {{ product[3] or 'No Model' }} (Stock: {{ product[5] }})</option>
{% endfor %}
</select>
</div>

<div class="serial-list" id="serialList">
<div style="padding: 20px; text-align: center; color: #999;">No serials scanned yet. Start scanning!</div>
</div>

<div style="margin-top: 20px;">
<button class="btn btn-success" onclick="saveAllSerials()">💾 Save All ({{ serials|length }} items)</button>
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
<input type="email" name="email" placeholder="Email" required>
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<select name="permission">
<option value="view">View Only</option>
<option value="full">Full Access</option>
</select>
<button type="submit" class="btn btn-success">Add User</button>
</form>
</div>

<h3>Existing Users</h3>
<table>
<thead>
<th>Email</th><th>Username</th><th>Role</th><th>Permission</th><th>Actions</th>
</thead>
<tbody>
{% for user in users %}
<tr>
<td>{{ user[1] }}</td>
<td>{{ user[3] }}</td>
<td>{{ user[4] }}</td>
<td><span class="permission-{{ 'full' if user[5] == 'full' else 'view' }}">{{ user[5] | upper }}</span></td>
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
</style>
</head>
<body>
<div class="container">
<div class="header">
<h2>📋 Material Take Transactions</h2>
<button class="btn-back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<input type="text" class="search-box" id="searchInput" placeholder="Search by Estimate Number or Product..." onkeyup="searchTable()">

<table id="transactionsTable">
<thead>
<th>Date</th><th>Product</th><th>Serial #</th><th>Quantity</th><th>Estimate Number</th><th>Taken By</th>
</thead>
<tbody>
{% for t in transactions %}
<tr>
<td>{{ t[6] }}</td>
<td>{{ t[2] }}</td>
<td>{{ t[3] or '-' }}</td>
<td>{{ t[4] }}</td>
<td><strong>{{ t[5] }}</strong></td>
<td>{{ t[7] }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

<script>
function searchTable() {
    let input = document.getElementById('searchInput');
    let filter = input.value.toLowerCase();
    let rows = document.querySelectorAll('#transactionsTable tbody tr');
    
    rows.forEach(row => {
        let text = row.innerText.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
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
                        <p><strong>Stock:</strong> ${data.stock} units</p>
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
            session['role'] = user[4]
            session['permission'] = user[5]
            return redirect('/dashboard')
        else:
            return render_template_string(LOGIN_TEMPLATE, error='Invalid email or password')
    
    return render_template_string(LOGIN_TEMPLATE)

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
    
    c.execute("SELECT COUNT(*) FROM transactions")
    total_taken = c.fetchone()[0]
    conn.close()
    
    total_products = len(products)
    low_stock = sum(1 for p in products if p[5] < 10)
    total_value = sum(p[5] * p[6] for p in products)
    
    from datetime import datetime
    now = datetime.now().strftime('%Y%m%d')
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                 products=products,
                                 brands=brands,
                                 categories=categories,
                                 total_products=total_products, 
                                 low_stock=low_stock, 
                                 total_value=f"{total_value:.2f}",
                                 total_taken=total_taken,
                                 now=now,
                                 username=session.get('username', 'User'),
                                 permission=session.get('permission', 'view'))

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT name FROM products WHERE name IS NOT NULL")
    product_names = [row[0] for row in c.fetchall()]
    
    c.execute("SELECT DISTINCT model_number FROM products WHERE model_number IS NOT NULL AND model_number != ''")
    models = [row[0] for row in c.fetchall()]
    
    c.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != ''")
    brands = [row[0] for row in c.fetchall()]
    
    c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        model_number = request.form.get('model_number', '')
        serial_number = request.form.get('serial_number', '')
        stock = int(request.form['stock'])
        price = float(request.form['price'])
        brand = request.form.get('brand', '')
        category = request.form.get('category', '')
        rack_number = request.form.get('rack_number', '')
        shelf_number = request.form.get('shelf_number', '')
        barcode = request.form.get('barcode', '')
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("""INSERT INTO products 
                     (name, sku, model_number, serial_number, stock, price, brand, category, rack_number, shelf_number, barcode) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (name, sku, model_number, serial_number, stock, price, brand, category, rack_number, shelf_number, barcode))
        conn.commit()
        conn.close()
        
        return redirect('/dashboard')
    
    return render_template_string(ADD_TEMPLATE, 
                                 product_names=product_names,
                                 models=models,
                                 brands=brands,
                                 categories=categories)

@app.route('/multi-scan')
def multi_scan():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT id, name, model_number, stock FROM products")
    products = c.fetchall()
    conn.close()
    
    return render_template_string(MULTI_SCAN_TEMPLATE, products=products, serials=[])

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
    
    # Get product info
    c.execute("SELECT name, stock FROM products WHERE id=?", (product_id,))
    product = c.fetchone()
    
    if product:
        # Update stock
        new_stock = product[1] + len(serials)
        c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))
        
        # Add each serial as a separate transaction
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for serial in serials:
            c.execute("""INSERT INTO transactions 
                         (product_id, product_name, serial_number, quantity_taken, estimate_number, taken_by, date_taken, notes) 
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (product_id, product[0], serial, 1, estimate, session.get('username', 'admin'), now, 'Bulk scan addition'))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Added {len(serials)} items'})
    
    conn.close()
    return jsonify({'success': False, 'message': 'Product not found'})

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

@app.route('/add-user', methods=['POST'])
def add_user():
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    email = request.form['email']
    username = request.form['username']
    password = hash_password(request.form['password'])
    permission = request.form['permission']
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, username, password, role, permission) VALUES (?,?,?,?,?)",
                  (email, username, password, 'staff', permission))
        conn.commit()
    except:
        pass
    conn.close()
    
    return redirect('/users')

@app.route('/delete-user/<int:id>')
def delete_user(id):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    return redirect('/users')

@app.route('/take/<int:id>/<int:quantity>/<path:estimate>')
def take_material(id, quantity, estimate):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    c.execute("SELECT name, serial_number, stock FROM products WHERE id=?", (id,))
    product = c.fetchone()
    
    if product and product[2] >= quantity:
        new_stock = product[2] - quantity
        c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, id))
        
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute("""INSERT INTO transactions 
                     (product_id, product_name, serial_number, quantity_taken, estimate_number, taken_by, date_taken) 
                     VALUES (?,?,?,?,?,?,?)""",
                  (id, product[0], product[1], quantity, estimate, session.get('username', 'admin'), now))
        
        conn.commit()
    
    conn.close()
    return redirect('/dashboard')

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

@app.route('/barcode-scanner')
def barcode_scanner():
    if 'user_id' not in session:
        return redirect('/')
    return render_template_string(BARCODE_TEMPLATE)

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
            'price': product[6],
            'rack_number': product[9],
            'shelf_number': product[10]
        })
    return jsonify({'found': False})

@app.route('/delete/<int:id>')
def delete_product(id):
    if 'user_id' not in session:
        return redirect('/')
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
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
    
    if session.get('permission') != 'full' and session.get('role') != 'admin':
        return "Access Denied", 403
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("UPDATE products SET stock=? WHERE id=?", (stock, id))
    conn.commit()
    conn.close()
    
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
