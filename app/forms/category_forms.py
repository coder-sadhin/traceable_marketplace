from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    slug = StringField('URL Slug', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')
