from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from wtforms import StringField, FloatField, IntegerField, SubmitField, SelectField, PasswordField
from wtforms.validators import InputRequired
from flask_wtf import FlaskForm
from datetime import datetime, date
import os
from forms import RemoveItemForm, DecreaseQuantityForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_revenue = db.Column(db.Float, nullable=False, default=0.0)
    last_production_date = db.Column(db.Date, nullable=False, default=date.today)
    sold_today = db.Column(db.Integer, nullable=False, default=0)
    revenue_today = db.Column(db.Float, nullable=False, default=0.0)
    last_sale_date = db.Column(db.Date, nullable=False, default=date.today)
    total_produced = db.Column(db.Integer, nullable=False, default=0)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class DailyTotal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    total_revenue = db.Column(db.Float, nullable=False, default=0.0)

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class ItemForm(FlaskForm):
    item = SelectField('Artikull', choices=[], coerce=int)
    quantity = IntegerField('Sasia', validators=[InputRequired()])
    submit = SubmitField('Shitur')

class ProduceForm(FlaskForm):
    item = SelectField('Artikull', choices=[], coerce=int)
    quantity = IntegerField('Sasia', validators=[InputRequired()])
    submit = SubmitField('Prodhuar')

class AddItemForm(FlaskForm):
    name = StringField('Emri i Artikullit', validators=[InputRequired()])
    price = FloatField('Çmimi', validators=[InputRequired()])
    submit = SubmitField('Shto Artikullin')

class InventoryItemForm(FlaskForm):
    name = StringField('Emri i Artikullit', validators=[InputRequired()])
    quantity = IntegerField('Sasia', validators=[InputRequired()])
    price_per_unit = FloatField('Çmimi për Njësi', validators=[InputRequired()])
    submit = SubmitField('Shto në Inventar')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('admin'))
        return render_template('login.html', form=form, message='Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    form = ItemForm()
    form.item.choices = [(item.id, item.name) for item in Item.query.all()]
    
    if request.method == 'POST' and form.validate():
        item = Item.query.get(form.item.data)
        if not item:
            return render_template('sell.html', form=form, message='Item not found')

        # Check if the item has been produced today
        if item.last_production_date < date.today():
            return render_template('sell.html', form=form, message=f'{item.name} nuk jane prodhuar sot.')

        if item.quantity < form.quantity.data:
            return render_template('sell.html', form=form, message=f'Nuk ka mjaftueshem {item.name} ne gjendje.')

        # Calculate total sale for the item and update totals
        total_sale = form.quantity.data * item.price
        item.total_revenue += total_sale
        item.quantity -= form.quantity.data

        # Track today's sales
        item.sold_today += form.quantity.data
        item.revenue_today += total_sale
        item.last_sale_date = date.today()

        # Update or create daily total
        daily_total = DailyTotal.query.filter_by(date=date.today()).first()
        if not daily_total:
            daily_total = DailyTotal(date=date.today(), total_revenue=total_sale)
            db.session.add(daily_total)
        else:
            daily_total.total_revenue += total_sale
        
        db.session.commit()
        return render_template('sell.html', form=form, message=f'Sold {form.quantity.data} of {item.name}')

    return render_template('sell.html', form=form)


@app.route('/produce', methods=['GET', 'POST'])
def produce():
    form = ProduceForm()
    form.item.choices = [(item.id, item.name) for item in Item.query.all()]
    if form.validate_on_submit():
        item = Item.query.get(form.item.data)
        if item.last_production_date < date.today():
            item.quantity = 0  # Reset stock at the beginning of a new day
        item.quantity += form.quantity.data
        item.total_produced += form.quantity.data
        item.last_production_date = date.today()  # Update the last production date
        db.session.commit()
        return render_template('produce.html', form=form, message=f'Produced {form.quantity.data} of {item.name}')
    return render_template('produce.html', form=form)


@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/generate_sold_items', methods=['POST'])
@login_required
def generate_sold_items():
    items = Item.query.all()
    sold_items = [
        {'name': item.name, 'quantity': item.total_produced - item.quantity, 'total_revenue': item.total_revenue}
        for item in items if item.total_revenue > 0
    ]
    return render_template('sold_items.html', sold_items=sold_items)

@app.route('/generate_remaining_items', methods=['POST'])
@login_required
def generate_remaining_items():
    items = Item.query.all()
    remaining_items = [
        {'name': item.name, 'quantity': item.quantity}
        for item in items if item.quantity > 0
    ]
    return render_template('remaining_items.html', remaining_items=remaining_items)

@app.route('/generate_daily_total', methods=['POST'])
@login_required
def generate_daily_total():
    today = date.today()
    daily_total = DailyTotal.query.filter_by(date=today).first()
    items = Item.query.filter(Item.last_sale_date == today).all()

    if daily_total:
        total_revenue = daily_total.total_revenue
    else:
        total_revenue = 0.0

    sold_items = [
        {'name': item.name, 'quantity': item.sold_today, 'total_revenue': item.revenue_today}
        for item in items if item.sold_today > 0
    ]

    return render_template('daily_total.html', date=today, total_revenue=total_revenue, sold_items=sold_items)

@app.route('/generate_monthly_total', methods=['POST'])
@login_required
def generate_monthly_total():
    current_date = date.today()
    current_month = current_date.month
    current_year = current_date.year
    
    # Get all daily totals for the current month and year
    monthly_totals = DailyTotal.query.filter(
        db.extract('month', DailyTotal.date) == current_month,
        db.extract('year', DailyTotal.date) == current_year
    ).all()

    items = Item.query.all()
    item_totals = {item.name: {'quantity': 0, 'total_revenue': 0.0} for item in items}

    for daily_total in monthly_totals:
        for item in items:
            item_totals[item.name]['quantity'] += item.quantity
            item_totals[item.name]['total_revenue'] += item.total_revenue

    grand_total = sum(total.total_revenue for total in monthly_totals)
    
    return render_template(
        'monthly_total.html', 
        monthly_totals=monthly_totals, 
        item_totals=item_totals, 
        grand_total=grand_total, 
        current_date=current_date
    )

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    form = AddItemForm()
    if form.validate_on_submit():
        new_item = Item(
            name=form.name.data,
            price=form.price.data,
            quantity=0,
            total_revenue=0.0,
            last_production_date=date.today()
        )
        db.session.add(new_item)
        db.session.commit()
    return render_template('add_item.html', form=form)

@app.route('/add_inventory_item', methods=['GET', 'POST'])
@login_required
def add_inventory_item():
    form = InventoryItemForm()
    if form.validate_on_submit():
        new_inventory_item = InventoryItem(
            name=form.name.data,
            quantity=form.quantity.data,
            price_per_unit=form.price_per_unit.data
        )
        db.session.add(new_inventory_item)
        db.session.commit()
    return render_template('add_inventory_item.html', form=form)
@app.route('/remove_inventory_item', methods=['GET', 'POST'])
@login_required
def remove_inventory_item():
    form = RemoveItemForm()
    form.item.choices = [(item.id, item.name) for item in InventoryItem.query.all()]
    if form.validate_on_submit():
        item = InventoryItem.query.get(form.item.data)
        db.session.delete(item)
        db.session.commit()
    return render_template('remove_inventory_item.html', form=form)

@app.route('/decrease_inventory_quantity', methods=['GET', 'POST'])
@login_required
def decrease_inventory_quantity():
    form = DecreaseQuantityForm()
    form.item.choices = [(item.id, item.name) for item in InventoryItem.query.all()]
    if form.validate_on_submit():
        item = InventoryItem.query.get(form.item.data)
        if item:
            item.quantity -= form.quantity.data
            if item.quantity < 0:
                item.quantity = 0
            db.session.commit()
    return render_template('decrease_inventory_quantity.html', form=form)

@app.route('/reset_inventory', methods=['POST'])
@login_required
def reset_inventory():
    InventoryItem.query.delete()
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/view_inventory', methods=['GET'])
@login_required
def view_inventory():
    inventory_items = InventoryItem.query.all()
    return render_template('view_inventory.html', inventory_items=inventory_items)

@app.route('/view_db')
@login_required
def view_db():
    items = Item.query.all()
    users = User.query.all()
    daily_totals = DailyTotal.query.all()
    return render_template('view_db.html', items=items, users=users, daily_totals=daily_totals)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
