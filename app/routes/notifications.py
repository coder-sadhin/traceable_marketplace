from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, Response, current_app
from flask_login import login_required, current_user
from app import db
from app.models.notification import Notification
from app.models.announcement import Announcement
from app.utils.notifications import get_unread_count

bp = Blueprint('notifications', __name__)

@bp.route('/')
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    # Include active announcements in the notification feed
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.created_at.desc()).all()
    return render_template('notifications/list.html', notifications=notifications, announcements=announcements)

@bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('notifications.list_notifications'))
    notification.mark_as_read()
    db.session.commit()
    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications.list_notifications'))

@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.list_notifications'))

@bp.route('/unread-count')
@login_required
def unread_count():
    return jsonify({'count': get_unread_count(current_user.id)})

@bp.route('/stream')
@login_required
def stream():
    # Capture user_id and app BEFORE entering the generator
    # Both current_user and app context are thread-local and lost inside the generator
    user_id = current_user.id
    app = current_app._get_current_object()
    
    def generate():
        import json, time
        try:
            with app.app_context():
                count = get_unread_count(user_id)
                yield f"data: {json.dumps({'count': count})}\n\n"
            # Keep connection alive, check every 15 seconds
            while True:
                time.sleep(15)
                with app.app_context():
                    count = get_unread_count(user_id)
                    yield f"data: {json.dumps({'count': count})}\n\n"
        except GeneratorExit:
            pass
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
