from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'subscriptions.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============ MODELS ============

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    city = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

class Box(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200))
    items = db.Column(db.Text)
    frequency = db.Column(db.String(20), default='monthly')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscriptions = db.relationship('Subscription', backref='box', lazy=True)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    box_id = db.Column(db.Integer, db.ForeignKey('box.id'), nullable=False)
    status = db.Column(db.String(20), default='active')
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    next_delivery = db.Column(db.DateTime)
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    box_id = db.Column(db.Integer, db.ForeignKey('box.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    box = db.relationship('Box', backref='orders', lazy=True)

# ============ AUTH DECORATORS ============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('سجل دخولك أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('ليس لديك صلاحية', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ============ ROUTES ============

@app.route('/')
def index():
    boxes = Box.query.filter_by(is_active=True).all()
    return render_template('index.html', boxes=boxes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        city = request.form.get('city')
        
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مسجل مسبقاً', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            phone=phone,
            city=city
        )
        db.session.add(user)
        db.session.commit()
        flash('تم إنشاء حسابك بنجاح! سجل دخولك', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_admin'] = user.is_admin
            flash(f'أهلاً {user.name}!', 'success')
            return redirect(url_for('index'))
        
        flash('بيانات الدخول غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('index'))

@app.route('/box/<int:box_id>')
def box_detail(box_id):
    box = Box.query.get_or_404(box_id)
    return render_template('box_detail.html', box=box)

@app.route('/subscribe/<int:box_id>', methods=['POST'])
@login_required
def subscribe(box_id):
    box = Box.query.get_or_404(box_id)
    address = request.form.get('address')
    
    if not address:
        flash('أدخل عنوان التوصيل', 'danger')
        return redirect(url_for('box_detail', box_id=box_id))
    
    # Check if already subscribed
    existing = Subscription.query.filter_by(
        user_id=session['user_id'], 
        box_id=box_id, 
        status='active'
    ).first()
    
    if existing:
        flash('أنت مشترك بالفعل في هذا الصندوق', 'warning')
        return redirect(url_for('my_subscriptions'))
    
    next_delivery = datetime.utcnow() + timedelta(days=30)
    
    subscription = Subscription(
        user_id=session['user_id'],
        box_id=box_id,
        address=address,
        next_delivery=next_delivery
    )
    db.session.add(subscription)
    
    order = Order(
        user_id=session['user_id'],
        box_id=box_id,
        amount=box.price,
        status='confirmed',
        payment_method='cash_on_delivery'
    )
    db.session.add(order)
    db.session.commit()
    
    flash(f'تم الاشتراك في {box.name} بنجاح! 🎉', 'success')
    return redirect(url_for('my_subscriptions'))

@app.route('/my-subscriptions')
@login_required
def my_subscriptions():
    subs = Subscription.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_subscriptions.html', subscriptions=subs)

@app.route('/cancel-subscription/<int:sub_id>', methods=['POST'])
@login_required
def cancel_subscription(sub_id):
    sub = Subscription.query.get_or_404(sub_id)
    if sub.user_id != session['user_id']:
        flash('غير مصرح', 'danger')
        return redirect(url_for('my_subscriptions'))
    
    sub.status = 'cancelled'
    db.session.commit()
    flash('تم إلغاء الاشتراك', 'info')
    return redirect(url_for('my_subscriptions'))

# ============ ADMIN ROUTES ============

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_boxes = Box.query.count()
    total_subs = Subscription.query.filter_by(status='active').count()
    total_revenue = db.session.query(db.func.sum(Order.amount)).filter_by(status='confirmed').scalar() or 0
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_boxes=total_boxes,
                         total_subs=total_subs,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders)

@app.route('/admin/boxes')
@admin_required
def admin_boxes():
    boxes = Box.query.all()
    return render_template('admin/boxes.html', boxes=boxes)

@app.route('/admin/boxes/add', methods=['GET', 'POST'])
@admin_required
def add_box():
    if request.method == 'POST':
        box = Box(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=float(request.form.get('price')),
            category=request.form.get('category'),
            items=request.form.get('items'),
            image=request.form.get('image', ''),
            frequency=request.form.get('frequency', 'monthly')
        )
        db.session.add(box)
        db.session.commit()
        flash('تمت إضافة الصندوق بنجاح', 'success')
        return redirect(url_for('admin_boxes'))
    
    return render_template('admin/add_box.html')

@app.route('/admin/boxes/edit/<int:box_id>', methods=['GET', 'POST'])
@admin_required
def edit_box(box_id):
    box = Box.query.get_or_404(box_id)
    if request.method == 'POST':
        box.name = request.form.get('name')
        box.description = request.form.get('description')
        box.price = float(request.form.get('price'))
        box.category = request.form.get('category')
        box.items = request.form.get('items')
        box.image = request.form.get('image', '')
        box.frequency = request.form.get('frequency', 'monthly')
        db.session.commit()
        flash('تم تحديث الصندوق', 'success')
        return redirect(url_for('admin_boxes'))
    
    return render_template('admin/edit_box.html', box=box)

@app.route('/admin/subscriptions')
@admin_required
def admin_subscriptions():
    subs = Subscription.query.all()
    return render_template('admin/subscriptions.html', subscriptions=subs)

# ============ API ============

@app.route('/api/boxes')
def api_boxes():
    boxes = Box.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'description': b.description,
        'price': b.price,
        'category': b.category,
        'image': b.image
    } for b in boxes])

# ============ SEED DATA ============

def seed_data():
    if Box.query.first():
        return
    
    boxes = [
        Box(name='صندوق القهوة المختصة', description='أفضل أنواع القهوة المختصة من مزارع مختارة بعناية. كل شهر تشكيلة جديدة من البن المحمص طازجاً.', price=89, category='قهوة', items='بن مختص 250غ، طريقة تحضير، بطاقة معلومات', image='https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400'),
        Box(name='صندوق العناية بالبشرة', description='منتجات عناية طبيعية بالبشرة من ماركات موثوقة. كريمات، سيروم، وأقنعة طبيعية.', price=149, category='عناية', items='سيروم فيتامين م، كريم ترطيب، قناع طبيعي', image='https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=400'),
        Box(name='صندوق الكتب', description='كتابين مختارين بعناية من أفضل الكتب العربية والعالمية المترجمة.', price=59, category='كتب', items='كتابين، ملخص، علامة مرجعية', image='https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400'),
        Box(name='صندوق الحلويات الشرقية', description='حلويات شرقية طازجة من أفضل الحلويات. بقلاوة، كنافة، وغريبة.', price=79, category='حلويات', items='تشكيلة حلويات 500غ', image='https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400'),
        Box(name='صندوق التوابل والبهارات', description='بهارات وتوابل فاخرة من مختلف أنحاء العالم. وصفات حصرية مع كل صندوق.', price=45, category='مطبخ', items='5 بهارات فاخرة، وصفات', image='https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400'),
        Box(name='صندوق اللياقة', description='مكملات غذائية وأدوات رياضية بسيطة لبداية رحلتك الرياضية.', price=199, category='رياضة', items='بروتين، أدوات رياضية، خطة تمارين', image='https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400'),
    ]
    
    for box in boxes:
        db.session.add(box)
    
    # Create admin user
    admin = User(
        name='المدير',
        email='admin@box.com',
        password=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    
    db.session.commit()
    print('✅ Seed data added!')

# ============ INIT ============

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
