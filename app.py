from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-2024'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize database
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT, password TEXT, role TEXT)''')
    
    # Create products table with rack and shelf
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, 
                  name TEXT, 
                  sku TEXT, 
                  stock INTEGER, 
                  price REAL, 
                  brand TEXT, 
                  category TEXT,
                  rack_number TEXT,
                  shelf_number TEXT)''')
    
    # Create transactions table for tracking taken materials
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY,
                  product_id INTEGER,
                  product_name TEXT,
                  quantity_taken INTEGER,
                  estimate_number TEXT,
                  taken_by TEXT,
                  date_taken TEXT,
                  notes TEXT,
                  FOREIGN KEY (product_id) REFERENCES products(id))''')
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE email=?", ('musthafa@purplerock.com',))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password, role) VALUES (?,?,?)",
                  ('musthafa@purplerock.com', hash_password('Limara9*'), 'admin'))
        
        # Add sample products with rack/shelf
        sample_products = [
            ('Laptop Pro', 'LAP001', 10, 999.99, 'Dell', 'Electronics', 'A1', 'S1'),
            ('Wireless Mouse', 'MOU001', 50, 29.99, 'Logitech', 'Accessories', 'B2', 'S3'),
            ('Mechanical Keyboard', 'KEY001', 5, 89.99, 'Corsair', 'Accessories', 'A2', 'S2'),
            ('24" Monitor', 'MON001', 8, 199.99, 'Samsung', 'Electronics', 'C1', 'S1'),
            ('USB-C Cable', 'CAB001', 100, 12.99, 'Anker', 'Accessories', 'B1', 'S4'),
        ]
        for p in sample_products:
            c.execute("INSERT INTO products (name, sku, stock, price, brand, category, rack_number, shelf_number) VALUES (?,?,?,?,?,?,?,?)", p)
    
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
<div class="nav-item" onclick="location.href='/logout'">🚪 Logout</div>
</div>

<div class="main-content">
<div class="header">
<h2>Dashboard</h2>
<span>👤 Admin</span>
</div>

<div class="stats">
<div class="stat-card"><div class="stat-number">{{ total_products }}</div><div class="stat-label">Total Products</div></div>
<div class="stat-card"><div class="stat-number">{{ low_stock }}</div><div class="stat-label">Low Stock</div></div>
<div class="stat-card"><div class="stat-number">${{ total_value }}</div><div class="stat-label">Inventory Value</div></div>
<div class="stat-card"><div class="stat-number">{{ total_taken }}</div><div class="stat-label">Items Taken</div></div>
</div>

<button class="add-btn" onclick="location.href='/add'">+ Add New Product</button>

<div class="table-container">
<h3>Product Inventory</h3>
<table>
<thead>
<th>Name</th><th>SKU</th><th>Stock</th><th>Price</th><th>Location</th><th>Actions</th>
</thead>
<tbody>
{% for product in products %}
<tr>
<td>{{ product[1] }}</td>
<td>{{ product[2] }}</td>
<td {% if product[3] < 10 %}class="low-stock"{% endif %}>{{ product[3] }}</td>
<td>${{ "%.2f"|format(product[4]) }}</td>
<td><span class="location-badge">Rack: {{ product[7] or 'N/A' }} | Shelf: {{ product[8] or 'N/A' }}</span></td>
<td>
<button class="btn-primary" onclick="updateStock({{ product[0] }}, {{ product[3] }})">Update</button>
<button class="btn-warning" onclick="takeMaterial({{ product[0] }}, '{{ product[1] }}')">Take</button>
<button class="btn-danger" onclick="deleteProduct({{ product[0] }})">Delete</button>
</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
</div>

<script>
function deleteProduct(id) {
    if(confirm('Delete this product?')) location.href = '/delete/' + id;
}
function updateStock(id, current) {
    let stock = prompt('Enter new stock quantity:', current);
    if(stock) location.href = '/update/' + id + '/' + stock;
}
function takeMaterial(id, name) {
    let estimate = prompt('Enter Estimate/Reference Number for this take:', 'EST-{{ now }}');
    let quantity = prompt('How many ' + name + '(s) are you taking?', '1');
    if(estimate && quantity) {
        location.href = '/take/' + id + '/' + quantity + '/' + encodeURIComponent(estimate);
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
.container { background: white; padding: 30px; border-radius: 12px; width: 550px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
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
<h2>➕ Add New Product</h2>
<form method="POST">
<input type="text" name="name" placeholder="Product Name" required>
<input type="text" name="sku" placeholder="SKU" required>
<div class="row">
<div><input type="number" name="stock" placeholder="Stock Quantity" required></div>
<div><input type="number" step="0.01" name="price" placeholder="Price" required></div>
</div>
<div class="row">
<div><input type="text" name="brand" placeholder="Brand"></div>
<div><input type="text" name="category" placeholder="Category"></div>
</div>
<h3>📍 Storage Location</h3>
<div class="row">
<div><input type="text" name="rack_number" placeholder="Rack Number (e.g., A1, B2)"></div>
<div><input type="text" name="shelf_number" placeholder="Shelf Number (e.g., S1, S2)"></div>
</div>
<button type="submit">💾 Save Product</button>
</form>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
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
<th>Date</th><th>Product</th><th>Quantity Taken</th><th>Estimate Number</th><th>Taken By</th><th>Notes</th>
</thead>
<tbody>
{% for t in transactions %}
<tr>
<td>{{ t[6] }}</td>
<td>{{ t[2] }}</td>
<td>{{ t[3] }}</td>
<td><strong>{{ t[4] }}</strong></td>
<td>{{ t[5] }}</td>
<td>{{ t[7] or '-' }}</td>
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
    
    c.execute("SELECT COUNT(*) FROM transactions")
    total_taken = c.fetchone()[0]
    conn.close()
    
    total_products = len(products)
    low_stock = sum(1 for p in products if p[3] < 10)
    total_value = sum(p[3] * p[4] for p in products)
    
    from datetime import datetime
    now = datetime.now().strftime('%Y%m%d')
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                 products=products, 
                                 total_products=total_products, 
                                 low_stock=low_stock, 
                                 total_value=f"{total_value:.2f}",
                                 total_taken=total_taken,
                                 now=now)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        stock = int(request.form['stock'])
        price = float(request.form['price'])
        brand = request.form.get('brand', '')
        category = request.form.get('category', '')
        rack_number = request.form.get('rack_number', '')
        shelf_number = request.form.get('shelf_number', '')
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (name, sku, stock, price, brand, category, rack_number, shelf_number) VALUES (?,?,?,?,?,?,?,?)",
                  (name, sku, stock, price, brand, category, rack_number, shelf_number))
        conn.commit()
        conn.close()
        
        return redirect('/dashboard')
    
    return render_template_string(ADD_TEMPLATE)

@app.route('/take/<int:id>/<int:quantity>/<path:estimate>')
def take_material(id, quantity, estimate):
    if 'user_id' not in session:
        return redirect('/')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Get product details
    c.execute("SELECT name, stock FROM products WHERE id=?", (id,))
    product = c.fetchone()
    
    if product and product[1] >= quantity:
        # Update stock
        new_stock = product[1] - quantity
        c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, id))
        
        # Record transaction
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute("""INSERT INTO transactions 
                     (product_id, product_name, quantity_taken, estimate_number, taken_by, date_taken) 
                     VALUES (?,?,?,?,?,?)""",
                  (id, product[0], quantity, estimate, session.get('user_id', 'admin'), now))
        
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
