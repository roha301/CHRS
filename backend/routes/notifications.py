import datetime
from flask import Blueprint, request, jsonify
from db import notifications_collection, users_collection
from middleware import auth_required

notifications_bp = Blueprint('notifications', __name__)


def create_notification(user_id, title, message, notif_type='info', link=''):
    """Create a notification for a specific user, or broadcast to all users if user_id is 'ALL'."""
    if user_id == 'ALL':
        # Broadcast: create notification for every user in the DB
        all_users = list(users_collection.find({}, {'_id': 1}))
        for u in all_users:
            _insert_notification(u['_id'], title, message, notif_type, link)
    else:
        _insert_notification(user_id, title, message, notif_type, link)


def _insert_notification(user_id, title, message, notif_type, link):
    notif = {
        '_id': str(int(datetime.datetime.now().timestamp() * 1000000)),  # microsecond precision for uniqueness
        'userId': user_id,
        'title': title,
        'message': message,
        'type': notif_type,    # 'event', 'booking', 'info'
        'link': link,
        'read': False,
        'createdAt': datetime.datetime.utcnow().isoformat()
    }
    notifications_collection.insert_one(notif)


# --- Get unread notifications ---
@notifications_bp.route('', methods=['GET'])
@auth_required
def get_notifications():
    try:
        user_id = request.user['id']
        notifications = list(notifications_collection.find(
            {'userId': user_id}
        ).sort('createdAt', -1).limit(50))  # most recent 50

        unread_count = sum(1 for n in notifications if not n.get('read', False))
        return jsonify({
            'notifications': notifications,
            'unreadCount': unread_count
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# --- Mark all notifications as read ---
@notifications_bp.route('/read', methods=['PUT'])
@auth_required
def mark_all_read():
    try:
        user_id = request.user['id']
        notifications_collection.update_many(
            {'userId': user_id, 'read': False},
            {'$set': {'read': True}}
        )
        return jsonify({'message': 'All notifications marked as read'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# --- Mark single notification as read ---
@notifications_bp.route('/<notif_id>/read', methods=['PUT'])
@auth_required
def mark_one_read(notif_id):
    try:
        notifications_collection.update_one(
            {'_id': notif_id, 'userId': request.user['id']},
            {'$set': {'read': True}}
        )
        return jsonify({'message': 'Notification marked as read'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500
