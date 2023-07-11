from functools import wraps
from flask import Flask, render_template, request, redirect, session,flash,url_for
import pymysql

db = pymysql.connect(
    host="localhost",
    user="root",
    password="Ranjith@24",
    database="ecommerce")
cursor = db.cursor()


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'your-secret-key'

def login_required(route_func):
    @wraps(route_func)
    def wrapped_route_func(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return route_func(*args, **kwargs)
    return wrapped_route_func

@app.route('/login', methods=['GET', 'POST'])
def login():
    error=None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Perform login validation
        cursor.execute("SELECT * FROM logins WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user[0]
            return redirect('/products')
        else:
            error = 'Invalid username or password'

    return render_template('login.html',error=error)


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    # Check if the user already exists
    cursor.execute("SELECT * FROM logins WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user:
        flash('User already exists', 'error')
        return redirect(url_for('login'))
    else:
        cursor.execute("""
            INSERT INTO logins (username, password)
            VALUES (%s, %s)
        """, (username, password))
        db.commit()

        flash('Registration successful', 'success')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')# Routes
@app.route('/')
def home():
    # Retrieve offers from database
    cursor.execute("SELECT title, description, image_url, discount FROM offers")
    offers = cursor.fetchall()
    # Convert the tuples to dictionaries
    offers = [{'title': offer[0], 'description': offer[1], 'image_url': offer[2], 'discount': offer[3]} for offer in
              offers]
    return render_template('home.html', offers=offers)


@app.route('/products')
@login_required
def products():
    # Retrieve products from database
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        cursor.execute("INSERT INTO products (name, price, description) VALUES (%s, %s, %s)",
                       (name, price, description))
        db.commit()
        return redirect('/products')
    else:
        return render_template('add_product.html')
@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form['product_id']
    username = session['username']

    # Retrieve product details
    cursor.execute("SELECT * FROM products WHERE id=%s", (product_id))
    product = cursor.fetchone()

    # Insert product details into the cart table
    cursor.execute("""
        INSERT INTO cart (product_id, product_name, price, description, username) 
        VALUES (%s, %s, %s, %s, %s)
    """, (product[0], product[1], product[2], product[3], username))
    db.commit()

    return redirect('/cart')
@app.route('/cart')
@login_required
def cart():
    # Retrieve cart items for the logged-in user
    cursor.execute("SELECT id, product_name, price, description FROM cart WHERE username = %s", (session['username']))
    cart_items = cursor.fetchall()

    return render_template('cart.html', cart_items=cart_items)

@app.route('/delete_from_cart', methods=['POST'])
@login_required
def delete_from_cart():
    item_id = request.form['item_id']
    username = session['username']

    # Delete item from the cart table
    cursor.execute("DELETE FROM cart WHERE id = %s AND username = %s", (item_id, username))
    db.commit()

    return redirect('/cart')


@app.route('/buy', methods=['POST'])
@login_required
def buy():
    item_id = request.form['item_id']
    username = session['username']

    # Retrieve item details
    cursor.execute("SELECT * FROM cart WHERE id=%s", (item_id,))
    item = cursor.fetchone()

    # Insert item details into the orders table
    cursor.execute("""
        INSERT INTO orderss (product_id, product_name, price, description, username) 
        VALUES (%s, %s, %s, %s, %s)
    """, (item[1], item[2], item[3], item[4], username))
    db.commit()

    # Remove item from the cart after placing an order
    cursor.execute("DELETE FROM cart WHERE id = %s AND username = %s", (item_id, username))
    db.commit()

    return redirect('/congrats')
@app.route('/congrats')
@login_required
def congrats():
    return render_template('congrats.html')
@app.route('/previous_orders')
@login_required
def previous_orders():
    username = session['username']

    # Fetch previous orders for the logged-in user
    cursor.execute("SELECT product_id, product_name, price, description FROM orderss WHERE username = %s", (username,))
    orders = cursor.fetchall()

    return render_template('previous_orders.html', orders=orders)
if __name__ == '__main__':
    app.run(debug=True,port="8080")