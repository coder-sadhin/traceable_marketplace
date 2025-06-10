from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.message import Message
from app.models.product import Product
from app.models.user import User
from app.forms.message_forms import MessageForm
from app.utils.notifications import notify_message_received
from datetime import datetime

bp = Blueprint('messages', __name__)

@bp.route('/')
@login_required
def inbox():
    messages = Message.query.filter_by(receiver_id=current_user.id, is_deleted_by_receiver=False)\
        .order_by(Message.created_at.desc()).all()
    return render_template('messages/inbox.html', messages=messages, now=datetime.utcnow(), unread_count=sum(1 for m in messages if not m.is_read))

@bp.route('/sent')
@login_required
def sent():
    messages = Message.query.filter_by(sender_id=current_user.id, is_deleted_by_sender=False)\
        .order_by(Message.created_at.desc()).all()
    return render_template('messages/sent.html', messages=messages, now=datetime.utcnow())

@bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    form = MessageForm()
    product_id = request.args.get('product_id', type=int) or request.form.get('product_id', type=int)
    receiver_id = request.args.get('receiver_id', type=int) or request.form.get('receiver_id', type=int)
    receiver_username = request.form.get('receiver_username', '')
    receiver = None
    product = None

    if request.method == 'GET':
        if product_id:
            product = Product.query.get_or_404(product_id)
            form.subject.data = f'Regarding: {product.name}'
            receiver_id = product.current_owner_id
        if receiver_id:
            receiver = User.query.get_or_404(receiver_id)
    elif request.method == 'POST':
        if receiver_username:
            receiver = User.query.filter_by(username=receiver_username).first()
            if receiver:
                receiver_id = receiver.id
            else:
                flash(f'User "{receiver_username}" not found.', 'error')
                return redirect(url_for('messages.compose'))

    if form.validate_on_submit():
        if not receiver_id:
            flash('Please specify a recipient.', 'error')
            return redirect(url_for('messages.compose'))

        if receiver_id == current_user.id:
            flash('Cannot send message to yourself.', 'error')
            return redirect(url_for('messages.compose'))

        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            product_id=product_id,
            subject=form.subject.data,
            body=form.body.data
        )
        db.session.add(message)
        db.session.commit()
        
        notify_message_received(
            user_id=receiver_id,
            sender_username=current_user.username
        )
        
        flash('Message sent!', 'success')
        return redirect(url_for('messages.inbox'))

    return render_template('messages/compose.html', form=form, receiver=receiver, product=product, receiver_id=receiver_id, product_id=product_id)

@bp.route('/<int:message_id>')
@login_required
def view_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('messages.inbox'))

    if message.receiver_id == current_user.id and not message.is_read:
        message.is_read = True
        db.session.commit()

    return render_template('messages/view.html', message=message)

@bp.route('/<int:message_id>/reply', methods=['GET', 'POST'])
@login_required
def reply(message_id):
    original = Message.query.get_or_404(message_id)
    if original.receiver_id != current_user.id and original.sender_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('messages.inbox'))

    form = MessageForm()
    reply_to = original.sender_id if original.receiver_id == current_user.id else original.receiver_id

    if request.method == 'GET':
        form.subject.data = f'Re: {original.subject}'

    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=reply_to,
            product_id=original.product_id,
            subject=form.subject.data,
            body=form.body.data
        )
        db.session.add(message)
        db.session.commit()
        
        notify_message_received(
            user_id=reply_to,
            sender_username=current_user.username
        )
        
        flash('Reply sent!', 'success')
        return redirect(url_for('messages.inbox'))

    return render_template('messages/compose.html', form=form, receiver=original.sender if original.receiver_id == current_user.id else original.receiver, product=original.product, receiver_id=reply_to, product_id=original.product_id, reply_subject=original.subject, reply_body='')

@bp.route('/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.sender_id == current_user.id:
        message.is_deleted_by_sender = True
    elif message.receiver_id == current_user.id:
        message.is_deleted_by_receiver = True
    else:
        flash('Unauthorized.', 'error')
        return redirect(url_for('messages.inbox'))

    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('messages.inbox'))
