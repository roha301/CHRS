import datetime
import socket
import os
from flask import Blueprint, request, jsonify
from db import events_collection, bookings_collection, halls_collection
from middleware import auth_required

events_bp = Blueprint('events', __name__)

def get_local_ip():
    """Return the best-guess LAN IP of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

@events_bp.route('/server-info', methods=['GET'])
def server_info():
    """Return the server's LAN IP so the frontend can build scannable QR URLs."""
    port = os.getenv('PORT', '5000')
    return jsonify({'ip': get_local_ip(), 'port': int(port)})



# --- Create Event (organizer who has booking) ---
@events_bp.route('', methods=['POST'])
@auth_required
def create_event():
    try:
        data = request.json
        event_id = str(int(datetime.datetime.now().timestamp() * 1000))
        
        # Store only the relative path – the frontend will prepend the
        # LAN IP at display time so QR codes always work.
        reg_path = f"/pages/event_register.html?eventId={event_id}"
        
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
            'registrationPath': reg_path,
            'participants': [],
            'createdAt': datetime.datetime.utcnow().isoformat()
        }
        events_collection.insert_one(event)
        return jsonify(event), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# --- Get all events (public) ---
@events_bp.route('', methods=['GET'])
def get_all_events():
    try:
        events = list(events_collection.find({}))
        return jsonify(events)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# --- Get my events (organizer) ---
@events_bp.route('/mine', methods=['GET'])
@auth_required
def get_my_events():
    try:
        events = list(events_collection.find({'organizerId': request.user['id']}))
        return jsonify(events)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# --- Get a single event (by ID) ---
@events_bp.route('/<event_id>', methods=['GET'])
def get_event(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        return jsonify(event)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# --- Register for event (QR scan / public) ---
@events_bp.route('/<event_id>/register', methods=['POST'])
def register_for_event(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404

        name = request.json.get('name', '').strip()
        year = request.json.get('year', '').strip()
        department = request.json.get('department', '').strip()
        if not name:
            return jsonify({'message': 'Name is required'}), 400
        if not year:
            return jsonify({'message': 'Year is required'}), 400
        if not department:
            return jsonify({'message': 'Department is required'}), 400

        if not event.get('requiresRegistration', False):
            return jsonify({'message': 'Registration is not enabled for this event'}), 400

        # Check for duplicate
        existing = [
            p for p in event.get('participants', [])
            if p.get('name', '').lower() == name.lower()
            and p.get('year', '').lower() == year.lower()
            and p.get('department', '').lower() == department.lower()
        ]
        if existing:
            return jsonify({'message': 'You are already registered for this event!'}), 400

        max_p = event.get('maxParticipants', 100)
        if len(event.get('participants', [])) >= max_p:
            return jsonify({'message': 'Event is full. Registration closed.'}), 400

        participant = {
            'name': name,
            'year': year,
            'department': department,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        events_collection.update_one(
            {'_id': event_id},
            {'$push': {'participants': participant}}
        )
        return jsonify({'message': f'Successfully registered for {event["title"]}!', 'participant': participant})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# --- Get event analytics (organizer only) ---
@events_bp.route('/<event_id>/analytics', methods=['GET'])
@auth_required
def event_analytics(event_id):
    try:
        event = events_collection.find_one({'_id': event_id})
        if not event:
            return jsonify({'message': 'Event not found'}), 404
        
        if event['organizerId'] != request.user['id'] and request.user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403

        participants = event.get('participants', [])
        return jsonify({
            'eventId': event_id,
            'title': event['title'],
            'date': event['date'],
            'totalRegistered': len(participants),
            'maxParticipants': event.get('maxParticipants', 100),
            'fillRate': round((len(participants) / max(event.get('maxParticipants', 100), 1)) * 100, 1),
            'participants': participants
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# --- Delete event (creator only) ---
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
