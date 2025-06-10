import os
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per file

def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', ALLOWED_IMAGE_EXTENSIONS)
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_image(filename):
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)

def secure_save_file(file, upload_subfolder, prefix=''):
    if file and file.filename and allowed_file(file.filename):
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            current_app.logger.warning(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE})")
            return None

        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        from datetime import datetime
        filename = f"{prefix}{name}_{int(datetime.utcnow().timestamp())}{ext}"
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_subfolder)
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return f"/static/uploads/{upload_subfolder}/{filename}"
    return None
