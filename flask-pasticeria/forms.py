from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, SelectField, PasswordField
from wtforms.validators import InputRequired

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

class RemoveItemForm(FlaskForm):
    item = SelectField('Artikull', choices=[], coerce=int)
    submit = SubmitField('Hiq Artikullin')

class DecreaseQuantityForm(FlaskForm):
    item = SelectField('Artikull', choices=[], coerce=int)
    quantity = IntegerField('Sasia për të Zbritur', validators=[InputRequired()])
    submit = SubmitField('Zbrit Sasinë')
