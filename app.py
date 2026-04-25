# Simplified templates for other pages (add these to avoid errors)
MULTI_SCAN_TEMPLATE = '<!DOCTYPE html><html><body><h2>Multi-Scan</h2><a href="/dashboard">Back</a></body></html>'
USERS_TEMPLATE = '<!DOCTYPE html><html><body><h2>User Management</h2><a href="/dashboard">Back</a></body></html>'
TRANSACTIONS_TEMPLATE = '<!DOCTYPE html><html><body><h2>Transactions</h2><a href="/dashboard">Back</a></body></html>'
BARCODE_TEMPLATE = '<!DOCTYPE html><html><body><h2>Barcode Scanner</h2><a href="/dashboard">Back</a></body></html>'
ACTIVITY_LOGS_TEMPLATE = '<!DOCTYPE html><html><body><h2>Activity Logs</h2><a href="/dashboard">Back</a></body></html>'
LOGO_SETTINGS_TEMPLATE = '<!DOCTYPE html><html><body><h2>Logo Settings</h2><a href="/dashboard">Back</a></body></html>'

USERS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>User Management</title>
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
.permission-full{background:#c6f6d5;color:#22543d}
.permission-view{background:#fed7d7;color:#742a2a}
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
<div class="header"><h2>👥 User Management</h2></div>

<div class="add-form">
<h3>Add New User</h3>
<form method="POST" action="/add-user">
<input type="email" name="email" placeholder="Email" required>
<input type="text" name="full_name" placeholder="Full Name" required>
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<select name="permission">
<option value="view">View Only</option>
<option value="full">Full Access</option>
</select>
<button type="submit" class="btn">Add User</button>
</form>
</div>

<h3>Existing Users</h3>
<table>
<thead><tr><th>Email</th><th>Full Name</th><th>Permission</th><th>Actions</th></tr></thead>
<tbody>
{% for user in users %}
<tr>
<td>{{ user[1] }}</td>
<td>{{ user[4] or '-' }}</td>
<td><span class="permission-badge permission-{{ 'full' if user[6] == 'full' else 'view' }}">{{ user[6] | upper }}</span></td>
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

TRANSACTIONS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Transactions</title>
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
<div class="header"><h2>📋 Transactions History</h2></div>

<input type="text" class="search-box" id="searchBox" placeholder="Search by estimate or product..." onkeyup="searchTable()">

<table id="transTable">
<thead><tr><th>Date</th><th>Estimate Number</th><th>Product</th><th>Quantity</th><th>Unit</th><th>Taken By</th></tr></thead>
<tbody>
{% for t in transactions %}
<tr>
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
function searchTable() {
    let input = document.getElementById('searchBox');
    let filter = input.value.toLowerCase();
    let rows = document.querySelectorAll('#transTable tbody tr');
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
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<script>
let lastScanned = '';
document.getElementById('barcodeInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        searchBarcode();
    }
});

function searchBarcode() {
    let barcode = document.getElementById('barcodeInput').value.trim();
    if (!barcode) return;
    
    fetch(`/api/product-by-barcode/${barcode}`)
        .then(res => res.json())
        .then(data => {
            if (data.found) {
                document.getElementById('result').innerHTML = `
                    <div class="product-found">
                        <h3>✅ Product Found!</h3>
                        <p><strong>Name:</strong> ${data.name}</p>
                        <p><strong>Model:</strong> ${data.model_number || '-'}</p>
                        <p><strong>Serial:</strong> ${data.serial_number || '-'}</p>
                        <p><strong>Stock:</strong> ${data.stock} ${data.unit_type}</p>
                        <p><strong>Location:</strong> Rack ${data.rack_number || 'N/A'} / Shelf ${data.shelf_number || 'N/A'}</p>
                        <button class="btn" onclick="location.href='/dashboard'">Go to Dashboard</button>
                    </div>
                `;
            } else {
                document.getElementById('result').innerHTML = `
                    <div class="product-notfound">
                        <h3>❌ Product Not Found</h3>
                        <p>No product found with barcode: ${barcode}</p>
                        <button class="btn" onclick="location.href='/add'">Add New Product</button>
                    </div>
                `;
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
.serial-item:hover{background:#e8e8e8}
.remove-btn{background:#e53e3e;color:white;border:none;border-radius:5px;padding:5px 10px;cursor:pointer}
select, .product-select{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:5px}
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

<select id="productSelect" class="product-select">
<option value="">-- Select Product --</option>
{% for p in products %}
<option value="{{ p[0] }}">{{ p[1] }} - {{ p[2] or 'No Model' }} (Stock: {{ p[3] }})</option>
{% endfor %}
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
        if (serial && !serials.includes(serial)) {
            serials.push(serial);
            updateList();
            this.value = '';
        }
    }
});

function updateList() {
    let container = document.getElementById('serialList');
    document.getElementById('count').innerText = serials.length;
    if (serials.length === 0) {
        container.innerHTML = '<div style="padding:20px;text-align:center;color:#999">No serials scanned yet</div>';
        return;
    }
    container.innerHTML = '';
    serials.forEach((s, i) => {
        container.innerHTML += `<div class="serial-item"><span>📦 ${s}</span><button class="remove-btn" onclick="removeSerial(${i})">Remove</button></div>`;
    });
}

function removeSerial(index) { serials.splice(index,1); updateList(); }
function clearAll() { if(confirm('Clear all?')) { serials = []; updateList(); } }

function saveSerials() {
    let productId = document.getElementById('productSelect').value;
    let estimate = prompt('Estimate Number for this batch:');
    if (!productId) { alert('Select product'); return; }
    if (!estimate) { alert('Enter estimate number'); return; }
    if (serials.length === 0) { alert('No serials to save'); return; }
    
    fetch('/api/save-multiple-serials', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId, serials: serials, estimate: estimate})
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) { alert('Saved ' + serials.length + ' items!'); serials = []; updateList(); }
        else alert('Error: ' + data.message);
    });
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
.header{background:white;padding:15px;border-radius:10px;margin-bottom:20px;display:flex;justify-content:space-between}
table{width:100%;background:white;border-radius:10px;border-collapse:collapse}
th,td{padding:12px;text-align:left;border-bottom:1px solid #ddd}
th{background:#f8f9fa}
.search-box{padding:10px;width:300px;margin-bottom:20px;border:1px solid #ddd;border-radius:5px}
.back{background:#718096;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}
.action-badge{background:#e2e8f0;padding:4px 8px;border-radius:12px;font-size:12px}
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
<thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Details</th></tr></thead>
<tbody>
{% for log in logs %}
<tr>
<td>{{ log[6] }}</td><td><strong>{{ log[2] }}</strong></td><td><span class="action-badge">{{ log[3] }}</span></td><td>{{ log[4] }}</td>
</tr>
{% endfor %}
</tbody>
</table>
<br>
<button class="back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>

<script>
function searchTable() {
    let input = document.getElementById('searchBox');
    let filter = input.value.toLowerCase();
    let rows = document.querySelectorAll('#logTable tbody tr');
    rows.forEach(row => { row.style.display = row.innerText.toLowerCase().includes(filter) ? '' : 'none'; });
}
</script>
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
<div class="preview">
<h3>Current Logo</h3>
{% if logo %}
<img src="{{ logo }}" class="current-logo">
{% else %}
<p>No logo uploaded. Using default 📦 icon.</p>
{% endif %}
</div>

<form method="POST" enctype="multipart/form-data">
<input type="file" name="logo" accept="image/*" required>
<button type="submit" class="btn btn-primary">Upload Logo</button>
</form>

<form method="POST" action="/remove-logo" style="margin-top:20px">
<button type="submit" class="btn btn-danger" onclick="return confirm('Remove logo?')">Remove Logo</button>
</form>

<button class="btn back" onclick="location.href='/dashboard'">← Back to Dashboard</button>
</div>
</div>
</body>
</html>
'''

# Also update the API route for product-by-barcode (add this if missing)
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
