from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    title = StringField('Review Title')
    body = TextAreaField('Your Review')
    submit = SubmitField('Submit Review')
