from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class ShippingForm(FlaskForm):
    tracking_number = StringField('Tracking Number', validators=[DataRequired()])
    shipping_carrier = StringField('Shipping Carrier (e.g., FedEx, UPS, DHL)')
    submit = SubmitField('Update Shipping')
