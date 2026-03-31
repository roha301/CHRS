import datetime
import os
import secrets
import socket

import jwt
from flask import Blueprint, request, jsonify

from db import events_collection
from middleware import auth_required, JWT_SECRET
from routes.notifications import create_notification

events_bp = Blueprint('events', __name__)


def get_local_ip():
    """Return the best-guess LAN IP of this machine."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return '127.0.0.1'


def build_registration_path(event_id):
    return f"/pages/event_register.html?eventId={event_id}"


def build_checkin_path(event_id, token):
    return f"/pages/event_checkin.html?eventId={event_id}&token={token}"


def build_participant_id():
    return secrets.token_hex(8)


def ensure_event_runtime_fields(event):
    if not event:
        return None

    update_fields = {}
    participants_changed = False
    normalized_participants = []
    for participant in event.get('participants', []):
        normalized = dict(participant)
        if not normalized.get('participantId'):
            normalized['participantId'] = build_participant_id()
            participants_changed = True
        if 'checkedIn' not in normalized:
            normalized['checkedIn'] = False
            participants_changed = True
        if 'checkedInAt' not in normalized:
            normalized['checkedInAt'] = ''
            participants_changed = True
        normalized_participants.append(normalized)

    if participants_changed:
        update_fields['participants'] = normalized_participants
        event['participants'] = normalized_participants

    if not event.get('registrationPath'):
        update_fields['registrationPath'] = build_registration_path(event['_id'])
        event['registrationPath'] = update_fields['registrationPath']

    if not event.get('checkInToken'):
        update_fields['checkInToken'] = secrets.token_urlsafe(24)
        event['checkInToken'] = update_fields['checkInToken']

    if update_fields:
        events_collection.update_one({'_id': event['_id']}, {'$set': update_fields})

    return event


def serialize_event(event, include_checkin_path=False, include_participants=False):
    if not event:
        return None

    event = ensure_event_runtime_fields(dict(event))
    payload = dict(event)
    participants = payload.get('participants', [])
    payload['participantCount'] = len(participants)
    payload['checkedInCount'] = sum(1 for participant in participants if participant.get('checkedIn'))
    payload['registrationPath'] = payload.get('registrationPath') or build_registration_path(payload['_id'])

    if include_checkin_path and payload.get('checkInToken'):
        payload['checkInPath'] = build_checkin_path(payload['_id'], payload['checkInToken'])

    if not include_participants:
        payload.pop('participants', None)

    payload.pop('checkInToken', None)
    return payload


def get_optional_user():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ', 1)[1].strip()
    if not token:
        return None

    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except Exception:
        return None


def can_manage_event(event, user):
    return bool(user) and (
        user.get('role') == 'admin' or event.get('organizerId') == user.get('id')
    )


def has_checkin_access(event, payload=None):
    user = getattr(request, 'user', None) or get_optional_user()
    if can_manage_event(event, user):
        return True

    request_payload = payload if payload is not None else (request.get_json(silent=True) or {})
    token = request.args.get('token') or request_payload.get('token')
    return bool(token and token == event.get('checkInToken'))


def build_attendance_summary(event):
    participants = event.get('participants', [])
    checked_in_count = sum(1 for participant in participants if participant.get('checkedIn'))
    total_registered = len(participants)
    no_show_count = max(total_registered - checked_in_count, 0)
    attendance_rate = round((checked_in_count / max(total_registered, 1)) * 100, 1) if total_registered else 0

    return {
        'eventId': event['_id'],
        'title': event.get('title', ''),
        'date': event.get('date', ''),
        'hallName': event.get('hallName', ''),
        'totalRegistered': total_registered,
        'checkedInCount': checked_in_count,
        'noShowCount': no_show_count,
        'attendanceRate': attendance_rate,
        'participants': participants
    }


@events_bp.route('/server-info', methods=['GET'])
def server_info():
    """Return the server's LAN IP so the frontend can build scannable QR URLs."""
    port = os.getenv('PORT', '5000')
    return jsonify({'ip': get_local_ip(), 'port': int(port)})


@events_bp.route('', methods=['POST'])
@auth_required
def create_event():
    try:
        data = request.json or {}
        event_id = str(int(datetime.datetime.now().timestamp() * 1000))
        checkin_token = secrets.token_urlsafe(24)

        event = {
            '_id': event_id,
            'organizerId': request.user['id'],
            'organizerName': data.get('organizerName') or request.user.get('name', 'Unknown'),
            'organizerYear': data.get('organizerYear', ''),
            'organizerDept': data.get('organizerDept', ''),
            'organizerEmail': data.get('organizerEmail', ''),
            'title': data.get('title', '').strip(),
            'description': data.get('description', ''),
            'hallId': data.get('hallId', ''),
            'hallName': data.get('hallName', ''),
            'date': data.get('date', ''),
            'startTime': data.get('startTime', ''),
            'endTime': data.get('endTime', ''),
            'club': data.get('club', 'None'),
            'category': data.get('category', 'General'),
            'requiresRegistration': data.get('requiresRegistration', False),
            'maxParticipants': int(data.get('maxParticipants', 100)),
            'registrationPath': build_registration_path(event_id),
            'checkInToken': checkin_token,
            'participants': [],
            'createdAt': datetime.datetime.utcnow().isoformat()
        }
        events_collection.insert_one(event)

        create_notification(
            'ALL',
            f'New Event: {event["title"]}',
            f'{event["title"]} on {event["date"]} at {event["hallName"]}. Check it out!',
            'event',
            '/pages/events.html'
        )

        return jsonify(serialize_event(event, include_checkin_path=True)), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('', methods=['GET'])
def get_all_events():
    try:
        events = [serialize_event(event) for event in events_collection.find({})]
        return jsonify(events)
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/mine', methods=['GET'])
@auth_required
def get_my_events():
    try:
        events = [
            serialize_event(event, include_checkin_path=True)
            for event in events_collection.find({'organizerId': request.user['id']})
        ]
        return jsonify(events)
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>', methods=['GET'])
def get_event(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        return jsonify(serialize_event(event))
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>/register', methods=['POST'])
def register_for_event(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        event = ensure_event_runtime_fields(event)
        payload = request.get_json(silent=True) or {}

        name = payload.get('name', '').strip()
        year = payload.get('year', '').strip()
        department = payload.get('department', '').strip()
        if not name:
            return jsonify({'message': 'Name is required'}), 400
        if not year:
            return jsonify({'message': 'Year is required'}), 400
        if not department:
            return jsonify({'message': 'Department is required'}), 400

        if not event.get('requiresRegistration', False):
            return jsonify({'message': 'Registration is not enabled for this event'}), 400

        existing = [
            participant for participant in event.get('participants', [])
            if participant.get('name', '').lower() == name.lower()
            and participant.get('year', '').lower() == year.lower()
            and participant.get('department', '').lower() == department.lower()
        ]
        if existing:
            return jsonify({'message': 'You are already registered for this event!'}), 400

        max_participants = event.get('maxParticipants', 100)
        if len(event.get('participants', [])) >= max_participants:
            return jsonify({'message': 'Event is full. Registration closed.'}), 400

        participant = {
            'participantId': build_participant_id(),
            'name': name,
            'year': year,
            'department': department,
            'checkedIn': False,
            'checkedInAt': '',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        events_collection.update_one(
            {'_id': event_id},
            {'$push': {'participants': participant}}
        )
        return jsonify({'message': f'Successfully registered for {event["title"]}!', 'participant': participant})
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>/self-checkin', methods=['POST'])
def self_checkin(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        event = ensure_event_runtime_fields(event)
        payload = request.get_json(silent=True) or {}
        name = payload.get('name', '').strip()

        if not name:
            return jsonify({'message': 'Name is required'}), 400

        participants = list(event.get('participants', []))
        target = None
        for participant in participants:
            if participant.get('name', '').lower() == name.lower():
                target = participant
                break

        if not target:
            return jsonify({'message': 'Name not found in the registration list. Please check your spelling.'}), 404

        if target.get('checkedIn'):
            return jsonify({'message': 'You are already checked in!'}), 400

        target['checkedIn'] = True
        target['checkedInAt'] = datetime.datetime.utcnow().isoformat()

        events_collection.update_one(
            {'_id': event_id},
            {'$set': {'participants': participants}}
        )

        return jsonify({'message': f'Successfully checked in for {event["title"]}!', 'participant': target})
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>/checkin/access', methods=['GET'])
@auth_required
def get_checkin_access(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        event = ensure_event_runtime_fields(event)
        if not can_manage_event(event, request.user):
            return jsonify({'message': 'Unauthorized'}), 403

        return jsonify({
            'eventId': event_id,
            'title': event.get('title', ''),
            'checkInPath': build_checkin_path(event_id, event['checkInToken'])
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>/checkin', methods=['GET'])
def get_checkin_desk(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        event = ensure_event_runtime_fields(event)
        if not has_checkin_access(event):
            return jsonify({'message': 'Check-in access denied'}), 403

        summary = build_attendance_summary(event)
        return jsonify({
            **summary,
            'organizerName': event.get('organizerName', ''),
            'startTime': event.get('startTime', ''),
            'endTime': event.get('endTime', ''),
            'club': event.get('club', 'None')
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>/participants/<participant_id>/checkin', methods=['PUT'])
def update_participant_checkin(event_id, participant_id):
    try:
        payload = request.get_json(silent=True) or {}
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        event = ensure_event_runtime_fields(event)
        if not has_checkin_access(event, payload):
            return jsonify({'message': 'Check-in access denied'}), 403

        checked_in = bool(payload.get('checkedIn', True))
        participants = list(event.get('participants', []))
        target = None
        for participant in participants:
            if participant.get('participantId') == participant_id:
                target = participant
                break

        if target is None:
            return jsonify({'message': 'Participant not found'}), 404

        target['checkedIn'] = checked_in
        target['checkedInAt'] = datetime.datetime.utcnow().isoformat() if checked_in else ''

        events_collection.update_one(
            {'_id': event_id},
            {'$set': {'participants': participants}}
        )

        checked_in_count = sum(1 for participant in participants if participant.get('checkedIn'))
        return jsonify({
            'message': 'Attendance updated',
            'participant': target,
            'checkedInCount': checked_in_count,
            'pendingCount': max(len(participants) - checked_in_count, 0)
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>/analytics', methods=['GET'])
@auth_required
def event_analytics(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        event = ensure_event_runtime_fields(event)
        if not can_manage_event(event, request.user):
            return jsonify({'message': 'Unauthorized'}), 403

        participants = event.get('participants', [])
        checked_in_count = sum(1 for participant in participants if participant.get('checkedIn'))

        return jsonify({
            'eventId': event_id,
            'title': event['title'],
            'date': event['date'],
            'totalRegistered': len(participants),
            'maxParticipants': event.get('maxParticipants', 100),
            'fillRate': round((len(participants) / max(event.get('maxParticipants', 100), 1)) * 100, 1),
            'checkedInCount': checked_in_count,
            'noShowCount': max(len(participants) - checked_in_count, 0),
            'attendanceRate': round((checked_in_count / max(len(participants), 1)) * 100, 1) if participants else 0,
            'participants': participants
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@events_bp.route('/<event_id>', methods=['DELETE'])
@auth_required
def delete_event(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        if event['organizerId'] != request.user['id']:
            return jsonify({'message': 'Only the event creator can delete this event'}), 403
        events_collection.delete_one({'_id': event_id})
        return jsonify({'message': 'Event deleted'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500
