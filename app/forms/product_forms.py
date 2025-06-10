from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, FileField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    product_type = SelectField('Product Type', choices=[
        ('physical', 'Physical Item'),
        ('digital', 'Digital Asset')
    ], validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('pottery', 'Pottery & Ceramics'),
        ('textiles', 'Textiles & Fabrics'),
        ('woodwork', 'Woodwork'),
        ('jewelry', 'Jewelry'),
        ('art', 'Art & Paintings'),
        ('other', 'Other')
    ])
    current_price = DecimalField('Price (¥)', validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    condition = SelectField('Condition', choices=[
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair')
    ], default='new')
    condition_description = TextAreaField('Condition Details')
    location = StringField('Location')
    dimensions = StringField('Dimensions')
    weight = StringField('Weight')
    image1 = FileField('Main Image')
    image2 = FileField('Image 2')
    image3 = FileField('Image 3')
    submit = SubmitField('List Product')

class ResaleForm(FlaskForm):
    current_price = DecimalField('Resale Price (¥)', validators=[
        DataRequired(),
        NumberRange(min=0.01)
    ])
    condition = SelectField('Condition', choices=[
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], validators=[DataRequired()])
    condition_description = TextAreaField('Condition Details')
    image1 = FileField('Current Photo 1')
    image2 = FileField('Current Photo 2')
    image3 = FileField('Current Photo 3')
    submit = SubmitField('List for Resale')
