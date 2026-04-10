from flask import Flask, render_template, request, redirect, session
import pyodbc

app = Flask(__name__)
app.secret_key = "secret123"

# SQL Server Connection
conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=DT-2UA8332510\SQLEXPRESS;"
    "DATABASE=erp_db;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()


# ================= LOGIN =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == "admin":
                return redirect('/admin')
            return redirect('/dashboard')

    return render_template('login.html')


# ================= SIGNUP =================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        business_type = request.form['business_type']

        cursor.execute(
            "INSERT INTO users (name, email, password, role, subscription,business_type) VALUES (?, ?, ?, 'user', 'active',?)",
            (name, email, password,business_type)
        )
        conn.commit()
        return redirect('/')

    return render_template('signup.html')


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']

    # USER INFO (important)
    cursor.execute("SELECT business_type, subscription FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    # 🔴 Subscription check
    if user.subscription != "active":
        return render_template("subscription_expired.html")

    # COMMON DATA (sabko milega)
    
    cursor.execute("SELECT ISNULL(SUM(quantity),0) FROM production WHERE user_id=?", (user_id,))
    total_production = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventory WHERE quantity < 5 AND user_id=?", (user_id,))
    low_stock = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bills WHERE user_id=?", (user_id,))
    total_bills = cursor.fetchone()[0]

    cursor.execute("SELECT ISNULL(SUM(price),0) FROM bills WHERE user_id=?", (user_id,))
    total_revenue = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id=?", (user_id,))
    total_items = cursor.fetchone()[0]
    

    # 🟢 BUSINESS TYPE BASED DASHBOARD
    if user.business_type == "shop":
        return render_template(
            "dashboard_shop.html",
            total_bills=total_bills,
            total_revenue=total_revenue,
            total_items=total_items
        )

    elif user.business_type == "restaurant":
        return render_template(
            "dashboard_restaurant.html",
            total_bills=total_bills,
            total_revenue=total_revenue
        )

    elif user.business_type == "ricemill":
        return render_template(
            "dashboard_ricemill.html",
            total_items=total_items
        )

    # fallback
    return render_template(
        "dashboard.html",
        total_bills=total_bills,
        total_revenue=total_revenue,
        total_items=total_items,
        total_production=total_production,
        low_stock=low_stock
    )

# ================= BILLING =================
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        item = request.form['item']
        price = request.form['price']

        cursor.execute(
            "INSERT INTO bills (item, price, user_id) VALUES (?, ?, ?)",
            (item, price, session['user_id'])
        )
        conn.commit()

    cursor.execute("SELECT * FROM bills WHERE user_id=?", (session['user_id'],))
    bills = cursor.fetchall()

    return render_template('billing.html', bills=bills)

@app.route('/delete_bill/<int:id>')
def delete_bill(id):
    cursor.execute("DELETE FROM bills WHERE id=?", (id,))
    conn.commit()
    return redirect('/billing')


# ================= INVENTORY =================
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        item = request.form['item']
        quantity = request.form['quantity']

        cursor.execute(
            "INSERT INTO inventory (item, quantity, user_id) VALUES (?, ?, ?)",
            (item, quantity, session['user_id'])
        )
        conn.commit()

    cursor.execute("SELECT * FROM inventory WHERE user_id=?", (session['user_id'],))
    items = cursor.fetchall()

    return render_template('inventory.html', items=items)

@app.route('/delete_item/<int:id>')
def delete_item(id):
    cursor.execute("DELETE FROM inventory WHERE id=?", (id,))
    conn.commit()
    return redirect('/inventory')

@app.route('/edit_item/<int:id>', methods=['GET','POST'])
def edit_item(id):

    if session.get('user_id') != 2:
        return "Unauthorized"

    if request.method == 'POST':
        item = request.form['item']
        quantity = request.form['quantity']

        cursor.execute(
            "UPDATE inventory SET item=?, quantity=? WHERE id=?",
            (item, quantity, id)
        )
        conn.commit()
        return redirect('/inventory')

    cursor.execute("SELECT * FROM inventory WHERE id=?", (id,))
    item = cursor.fetchone()

    return render_template('edit_item.html', item=item)

# production______________________________________

@app.route('/production', methods=['GET','POST'])
def production():

    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        item = request.form['item']
        quantity = request.form['quantity']

        cursor.execute(
            "INSERT INTO production (item, quantity, date, user_id) VALUES (?, ?, GETDATE(), ?)",
            (item, quantity, session['user_id'])
        )
        conn.commit()

    cursor.execute("SELECT * FROM production WHERE user_id=?", (session['user_id'],))
    data = cursor.fetchall()

    return render_template('production.html', data=data)





# Procurement
#
#
#







@app.route('/procurement', methods=['GET','POST'])
def procurement():

    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':

        supplier = request.form['supplier']
        mobile = request.form['mobile']
        address = request.form['address']
        aadhaar = request.form['aadhaar']

        paddy = request.form['paddy']
        moisture = request.form['moisture']

        weight = float(request.form['weight'])
        rate = float(request.form['rate'])

        total = weight * rate

        commission = request.form['commission']
        transport = request.form['transport']

        date = request.form['date']

        status = request.form['status']
        mode = request.form['mode']

        slip = request.form['slip']

        # ✅ STEP 1: INSERT PROCUREMENT
        cursor.execute("""
        INSERT INTO procurement
        (supplier_name, mobile, address, aadhaar, paddy_type, moisture,
        weight, rate, total_amount, commission, transport_cost,
        purchase_date, payment_status, payment_mode, slip_no, user_id)

        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (supplier, mobile, address, aadhaar, paddy, moisture,
         weight, rate, total, commission, transport,
         date, status, mode, slip, session['user_id'])
        )

        conn.commit()

        # ✅ STEP 2: INVENTORY AUTO UPDATE (inventory1)

        cursor.execute("""
        SELECT id, quantity FROM inventory1 
        WHERE item_name=? AND user_id=?
        """, (paddy, session['user_id']))

        item = cursor.fetchone()

        if item:
            new_qty = item.quantity + weight

            cursor.execute("""
            UPDATE inventory1 
            SET quantity=?, last_updated=GETDATE()
            WHERE id=?
            """, (new_qty, item.id))

        else:
            cursor.execute("""
            INSERT INTO inventory1 
            (item_name, category, quantity, unit, location, batch_no, entry_date, last_updated, min_stock, user_id)

            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                paddy,
                "Raw",
                weight,
                "Quintal",
                "Godown A",
                slip,
                date,
                date,
                50,
                session['user_id']
            ))

        conn.commit()

    # ✅ STEP 3: SHOW DATA
    cursor.execute("SELECT * FROM procurement WHERE user_id=?", (session['user_id'],))
    data = cursor.fetchall()

    return render_template("procurement.html", data=data)









######################## Inventory rice    e###############
######################                            ##############


@app.route('/inventory_rice')
def inventory_rice():

    if 'user_id' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM inventory1 WHERE user_id=?", (session['user_id'],))
    items = cursor.fetchall()

    return render_template("inventory_rice.html", items=items)


# CHECK existing item












# ================= ADMIN PANEL =================
@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect('/')

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    return render_template('admin.html', users=users)


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)