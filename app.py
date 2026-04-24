from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret123'

DB_PATH = 'database.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        username TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        sku TEXT UNIQUE,
        stock INTEGER,
        price REAL,
        brand TEXT,
        category TEXT
    )''')
    
    admin = conn.execute("SELECT * FROM users WHERE email = ?", ('musthafa@purplerock.com',)).fetchone()
    if not admin:
        conn.execute("INSERT INTO users (email, password, username) VALUES (?,?,?)",
                    ('musthafa@purplerock.com', generate_password_hash('Limara9*'), 'Admin'))
        
        samples = [
            ('Laptop Pro', 'LAP001', 10, 999.99, 'Dell', 'Electronics'),
            ('Wireless Mouse', 'MOU001', 50, 29.99, 'Logitech', 'Accessories'),
            ('Keyboard', 'KEY001', 5, 89.99, 'Corsair', 'Accessories'),
        ]
        for s in samples:
            conn.execute("INSERT INTO products (name, sku, stock, price, brand, category) VALUES (?,?,?,?,?,?)", s)
    
    conn.commit()
    conn.close()

# Simple login page
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: #667eea; }
        .box { background: white; padding: 40px; border-radius: 10px; width: 350px; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 10px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .error { color: red; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Inventory System</h2>
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

# Simple dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; background: #f0f2f5; }
        .header { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat { background: white; padding: 20px; border-radius: 10px; flex: 1; text-align: center; }
        .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
        table { width: 100%; background: white; border-radius: 10px; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        button { padding: 5px 10px; margin: 0 2px; cursor: pointer; }
        .add-btn { background: #48bb78; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin-bottom: 20px; cursor: pointer; }
        .logout { background: #e53e3e; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Inventory Dashboard</h2>
        <div><button class="logout" onclick="location.href='/logout'">Logout</button></div>
    </div>
    
    <div class="stats">
        <div class="stat"><div class="stat-number">{{ total_products }}</div><div>Total Products</div></div>
        <div class="stat"><div class="stat-number">{{ low_stock }}</div><div>Low Stock</div></div>
        <div class="stat"><div class="stat-number">${{ total_value }}</div><div>Inventory Value</div></div>
    </div>
    
    <button class="add-btn" onclick="location.href='/add'">+ Add Product</button>
    
    <table>
        <tr><th>Name</th><th>SKU</th><th>Stock</th><th>Price</th><th>Brand</th><th>Action</th></tr>
        {% for p in products %}
        <tr>
            <td>{{ p.name }}</td>
            <td>{{ p.sku }}</td>
            <td {% if p.stock < 10 %}style="color:red;font-weight:bold"{% endif %}>{{ p.stock }}</td>
            <td>${{ "%.2f"|format(p.price) }}</td>
            <td>{{ p.brand }}</td>
            <td>
                <button onclick="updateStock({{ p.id }}, {{ p.stock }})">Update Stock</button>
                <button onclick="deleteProduct({{ p.id }})" style="background:#e53e3e;color:white">Delete</button>
            </td>
        </tr>
        {% endfor %}
    </table>
    
    <script>
        function deleteProduct(id) {
            if(confirm('Delete this product?')) location.href = '/delete/' + id;
        }
        function updateStock(id, current) {
            let stock = prompt('Enter new stock:', current);
            if(stock) location.href = '/update/' + id + '/' + stock;
        }
    </script>
</body>
</html>
'''

# Add product page
ADD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Add Product</title>
    <style>
        body { font-family: Arial; padding: 40px; background: #f0f2f5; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        label { display: block; margin: 10px 0 5px; }
        input { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 5px; margin-top: 20px; cursor: pointer; }
        .back { background: #718096; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Add New Product</h2>
        <form method="POST">
            <label>Product Name:</label>
            <input type="text" name="name" required>
            <label>SKU:</label>
            <input type="text" name="sku" required>
            <label>Stock:</label>
            <input type="number" name="stock" required>
            <label>Price:</label>
            <input type="number" step="0.01" name="price" required>
            <label>Brand:</label>
            <input type="text" name="brand">
            <label>Category:</label>
            <input type="text" name="category">
            <button type="submit">Save Product</button>
        </form>
        <button class="back" onclick="location.href='/dashboard'">Back</button>
    </div>
</body>
</html>
'''

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/dashboard')
        return render_template_string(LOGIN_HTML, error='Invalid login')
    return render_template_string(LOGIN_HTML)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    total_products = len(products)
    low_stock = len([p for p in products if p['stock'] < 10])
    total_value = sum(p['stock'] * p['price'] for p in products)
    return render_template_string(DASHBOARD_HTML, products=products, total_products=total_products, low_stock=low_stock, total_value=f"{total_value:.2f}")

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect('/')
    if request.method == 'POST':
        conn = get_db()
        conn.execute("INSERT INTO products (name, sku, stock, price, brand, category) VALUES (?,?,?,?,?,?)",
                    (request.form['name'], request.form['sku'], int(request.form['stock']), float(request.form['price']), request.form.get('brand', ''), request.form.get('category', '')))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    return render_template_string(ADD_HTML)

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/update/<int:id>/<int:stock>')
def update(id, stock):
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    conn.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, id))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Start app
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
