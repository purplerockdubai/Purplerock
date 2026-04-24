from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import hashlib

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
    
    # Create products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, stock INTEGER, price REAL, brand TEXT, category TEXT)''')
    
    # Check if admin exists
    c.execute("SELECT * FROM users WHERE email=?", ('musthafa@purplerock.com',))
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password, role) VALUES (?,?,?)",
                  ('musthafa@purplerock.com', hash_password('Limara9*'), 'admin'))
        
        # Add sample products
        sample_products = [
            ('Laptop Pro', 'LAP001', 10, 999.99, 'Dell', 'Electronics'),
            ('Wireless Mouse', 'MOU001', 50, 29.99, 'Logitech', 'Accessories'),
            ('Mechanical Keyboard', 'KEY001', 5, 89.99, 'Corsair', 'Accessories'),
            ('24" Monitor', 'MON001', 8, 199.99, 'Samsung', 'Electronics'),
            ('USB-C Cable', 'CAB001', 100, 12.99, 'Anker', 'Accessories'),
        ]
        c.executemany("INSERT INTO products (name, sku, stock, price, brand, category) VALUES (?,?,?,?,?,?)", sample_products)
    
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
.sidebar { width: 260px; background: #1a1a2e; color: white; position: fixed; height: 100%; }
.sidebar-header { padding: 25px; text-align: center; border-bottom: 1px solid #2a2a4e; }
.nav-item { padding: 15px 25px; cursor: pointer; transition: 0.3s; }
.nav-item:hover { background: #2a2a4e; }
.main-content { margin-left: 260px; padding: 20px; }
.header { background: white; padding: 15px 25px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
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
.add-btn { background: #48bb78; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin-bottom: 20px; }
.low-stock { color: #e53e3e; font-weight: bold; }
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
</div>

<button class="add-btn" onclick="location.href='/add'">+ Add New Product</button>

<div class="table-container">
<table>
<thead>
<th>Name</th><th>SKU</th><th>Stock</th><th>Price</th><th>Brand</th><th>Category</th><th>Actions</th>
</thead>
<tbody>
{% for product in products %}
<tr>
<td>{{ product[1] }}</td>
<td>{{ product[2] }}</td>
<td {% if product[3] < 10 %}class="low-stock"{% endif %}>{{ product[3] }}</td>
<td>${{ "%.2f"|format(product[4]) }}</td>
<td>{{ product[5] }}</td>
<td>{{ product[6] }}</td>
<td>
<button class="btn-primary" onclick="updateStock({{ product[0] }}, {{ product[3] }})">Update</button>
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
</script>
</body>
</html>
'''

ADD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Add Product - Inventory Pro</title>
<style>
body { font-family: 'Segoe UI', Arial; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.container { background: white; padding: 30px; border-radius: 12px; width: 500px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
button { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px; font-size: 16px; }
.back { background: #718096; }
h2 { margin-bottom: 20px; color: #333; }
</style>
</head>
<body>
<div class="container">
<h2>➕ Add New Product</h2>
<form method="POST">
<input type="text" name="name" placeholder="Product Name" required>
<input type="text" name="sku" placeholder="SKU" required>
<input type="number" name="stock" placeholder="Stock Quantity" required>
<input type="number" step="0.01" name="price" placeholder="Price" required>
<input type="text" name="brand" placeholder="Brand">
<input type="text" name="category" placeholder="Category">
<button type="submit">💾 Save Product</button>
</form>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>
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
    conn.close()
    
    total_products = len(products)
    low_stock = sum(1 for p in products if p[3] < 10)
    total_value = sum(p[3] * p[4] for p in products)
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                 products=products, 
                                 total_products=total_products, 
                                 low_stock=low_stock, 
                                 total_value=f"{total_value:.2f}")

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
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (name, sku, stock, price, brand, category) VALUES (?,?,?,?,?,?)",
                  (name, sku, stock, price, brand, category))
        conn.commit()
        conn.close()
        
        return redirect('/dashboard')
    
    return render_template_string(ADD_TEMPLATE)

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
