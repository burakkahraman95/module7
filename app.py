from flask import Flask, render_template, redirect, url_for, request, session
import uuid
from database import create_tables, save_order, get_orders_by_session, get_all_orders, update_order_status

app = Flask(__name__)
app.secret_key = 'secret123'

VALID_STATUSES = ['Pending', 'Processing', 'Shipped', 'Delivered']

products = [
    {"id": 1, "name": "Wireless Headphones", "price": 79.99, "category": "Electronics",
     "description": "High-quality wireless headphones with noise cancellation and 30hr battery life."},
    {"id": 2, "name": "Leather Wallet", "price": 34.99, "category": "Accessories",
     "description": "Slim genuine leather wallet with RFID blocking protection."},
    {"id": 3, "name": "Running Shoes", "price": 119.99, "category": "Footwear",
     "description": "Lightweight running shoes built for all terrain and comfort."},
    {"id": 4, "name": "Coffee Maker", "price": 49.99, "category": "Kitchen",
     "description": "Brew the perfect cup every morning with programmable settings."},
    {"id": 5, "name": "Yoga Mat", "price": 29.99, "category": "Sports",
     "description": "Non-slip eco-friendly yoga mat with alignment guide lines."},
    {"id": 6, "name": "Sunglasses", "price": 59.99, "category": "Accessories",
     "description": "UV400 polarized sunglasses for stylish all-day comfort."},
]

create_tables()


def get_product_by_id(product_id):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


def ensure_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


@app.route('/')
def home():
    ensure_session_id()
    cart_count = sum(session.get('cart', {}).values())
    return render_template('index.html', products=products, cart_count=cart_count)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    ensure_session_id()
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    session['cart'] = cart
    return redirect(url_for('home'))


@app.route('/cart')
def cart():
    ensure_session_id()
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, qty in cart.items():
        product = get_product_by_id(int(product_id))
        if product:
            subtotal = product['price'] * qty
            cart_items.append({**product, 'qty': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    key = str(product_id)
    if key in cart:
        del cart[key]
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session['cart'] = {}
    return redirect(url_for('cart'))


@app.route('/place_order', methods=['POST'])
def place_order():
    session_id = ensure_session_id()
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart'))

    cart_items = []
    total = 0
    for product_id, qty in cart.items():
        product = get_product_by_id(int(product_id))
        if product:
            subtotal = product['price'] * qty
            cart_items.append({**product, 'qty': qty, 'subtotal': subtotal})
            total += subtotal

    order_id = save_order(session_id, cart_items, total)
    session['cart'] = {}
    return redirect(url_for('order_confirmation', order_id=order_id))


@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    session_id = ensure_session_id()
    orders = get_orders_by_session(session_id)
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return redirect(url_for('home'))
    return render_template('order_confirmation.html', order=order)


@app.route('/orders')
def orders():
    session_id = ensure_session_id()
    user_orders = get_orders_by_session(session_id)
    return render_template('orders.html', orders=user_orders)


@app.route('/admin/orders')
def admin_orders():
    all_orders = get_all_orders()
    return render_template('admin_orders.html', orders=all_orders, statuses=VALID_STATUSES)


@app.route('/admin/orders/update_status/<int:order_id>', methods=['POST'])
def admin_update_status(order_id):
    new_status = request.form.get('status')
    if new_status in VALID_STATUSES:
        update_order_status(order_id, new_status)
    return redirect(url_for('admin_orders'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
