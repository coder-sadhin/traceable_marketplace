import os
import qrcode
from flask import current_app, url_for

def generate_product_qr(product):
    """Generate a QR code for product traceability.
    
    Falls back to localhost if called without request context.
    """
    try:
        # Get URL dynamically from request
        traceability_url = url_for('main.trace_product', product_code=product.unique_code, _external=True)
    except RuntimeError:
        # Fallback to relative path if no request context
        traceability_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5001')}/trace/{product.unique_code}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(traceability_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color='black', back_color='white')
    
    filename = f"qr_{product.unique_code}.png"
    upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads'))
    filepath = os.path.join(upload_folder, 'qrcodes', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    img.save(filepath)
    
    return f"/static/uploads/qrcodes/{filename}"
