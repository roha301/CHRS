import datetime
import qrcode
import base64
import json
from io import BytesIO
from flask import Blueprint, request, jsonify
from db import bookings_collection, halls_collection, users_collection
from middleware import auth_required, admin_required
from routes.notifications import create_notification

bookings_bp = Blueprint('bookings', __name__)


def _parse_minutes(value):
    try:
        hour, minute = map(int, str(value).split(':'))
        return (hour * 60) + minute
    except Exception:
        return None


def _normalize_requested_resources(resources):
    if not isinstance(resources, list):
        return []
    normalized = []
    seen = set()
    for item in resources:
        value = str(item or '').strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(value)
    return normalized


def get_maintenance_conflicts(hall_id, date, start_time, end_time):
    hall = halls_collection.find_one({'_id': hall_id}, {'maintenanceWindows': 1, 'name': 1, 'resources': 1})
    if not hall:
        return []

    start_minutes = _parse_minutes(start_time)
    end_minutes = _parse_minutes(end_time)
    if start_minutes is None or end_minutes is None:
        return []

    conflicts = []
    for window in hall.get('maintenanceWindows', []):
        if window.get('date') != date:
            continue
        window_start = _parse_minutes(window.get('startTime'))
        window_end = _parse_minutes(window.get('endTime'))
        if window_start is None or window_end is None:
            continue
        if start_minutes < window_end and end_minutes > window_start:
            conflicts.append(window)
    return conflicts


def check_overlap(hall_id, date, start_time, end_time):
    return list(bookings_collection.find({
        'hallId': hall_id,
        'date': date,
        'status': {'$in': ['Pending', 'Approved']},
        'startTime': {'$lt': end_time},
        'endTime': {'$gt': start_time}
    }))

def find_nearest_slot(hall_id, date, duration_minutes):
    for h in range(8, 18):
        s_time = f"{h:02d}:00"
        e_hour = h + (duration_minutes // 60)
        e_min = duration_minutes % 60
        e_time = f"{e_hour:02d}:{e_min:02d}"
        
        if not check_overlap(hall_id, date, s_time, e_time) and not get_maintenance_conflicts(hall_id, date, s_time, e_time):
            return f"{s_time} - {e_time}"
    return "No available slots found for this date."

@bookings_bp.route('', methods=['POST'])
@auth_required
def create_booking():
    try:
        data = request.json
        hall_id = data.get('hallId')
        date = data.get('date')
        start_time = data.get('startTime')
        end_time = data.get('endTime')
        purpose = data.get('purpose')
        
        # New fields
        name = data.get('name')
        year = data.get('year')
        department = data.get('department')
        club = data.get('club')
        post = data.get('post')
        event_name = data.get('eventName')
        requested_resources = _normalize_requested_resources(data.get('requestedResources', []))
        
        user_id = request.user['id']
        hall = halls_collection.find_one({'_id': hall_id})
        if not hall:
            return jsonify({'message': 'Hall not found'}), 404

        start_minutes = _parse_minutes(start_time)
        end_minutes = _parse_minutes(end_time)
        if not date or start_minutes is None or end_minutes is None:
            return jsonify({'message': 'Booking date and time are required'}), 400
        if start_minutes >= end_minutes:
            return jsonify({'message': 'End time must be after the start time'}), 400

        available_resources = {str(item).strip().lower(): str(item).strip() for item in hall.get('resources', []) if str(item).strip()}
        invalid_resources = [item for item in requested_resources if item.lower() not in available_resources]
        if invalid_resources:
            return jsonify({
                'message': 'Some selected equipment is not available in this hall',
                'invalidResources': invalid_resources
            }), 400

        # Calculate duration
        duration = end_minutes - start_minutes

        # --- Past-time guard: can't book a slot whose start time has already passed ---
        try:
            booking_start_dt = datetime.datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
            if booking_start_dt < datetime.datetime.now():
                return jsonify({'message': 'Cannot book a slot in the past. Please choose a future time.'}), 400
        except Exception:
            pass

        maintenance_conflicts = get_maintenance_conflicts(hall_id, date, start_time, end_time)
        if maintenance_conflicts:
            window = maintenance_conflicts[0]
            return jsonify({
                'message': 'Hall is blocked for maintenance during this slot.',
                'suggestion': f"Maintenance window: {window.get('title', 'Maintenance')} ({window.get('startTime')} - {window.get('endTime')})"
            }), 409

        overlaps = check_overlap(hall_id, date, start_time, end_time)
        if overlaps:
            suggestion = find_nearest_slot(hall_id, date, duration)
            clashing = [{
                'eventName': o.get('eventName', 'Event'),
                'startTime': o.get('startTime'),
                'endTime': o.get('endTime'),
                'status': o.get('status')
            } for o in overlaps]
            return jsonify({
                'message': 'This time slot clashes with an existing booking.',
                'clashing': clashing,
                'suggestion': f"Nearest available slot: {suggestion}"
            }), 409

        booking = {
            '_id': str(int(datetime.datetime.now().timestamp() * 1000)),
            'userId': user_id,
            'hallId': hall_id,
            'name': name,
            'year': year,
            'department': department,
            'club': club,
            'post': post,
            'eventName': event_name,
            'requestedResources': requested_resources,
            'date': date,
            'startTime': start_time,
            'endTime': end_time,
            'purpose': purpose,
            'status': 'Pending',
            'createdAt': datetime.datetime.now().isoformat()
        }
        bookings_collection.insert_one(booking)
        return jsonify(booking), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

def _sweep_completed_status(b_list):
    now = datetime.datetime.now()
    for b in b_list:
        if b['status'] == 'Approved':
            try:
                end_dt_str = f"{b['date']} {b['endTime']}"
                end_dt = datetime.datetime.strptime(end_dt_str, '%Y-%m-%d %H:%M')
                if now > end_dt:
                    b['status'] = 'Completed'
                    bookings_collection.update_one({'_id': b['_id']}, {'$set': {'status': 'Completed'}})
            except Exception:
                pass

@bookings_bp.route('', methods=['GET'])
@auth_required
def get_user_bookings():
    user_id = request.user['id']
    user_bookings = list(bookings_collection.find({'userId': user_id}))
    _sweep_completed_status(user_bookings)
    for b in user_bookings:
        hall = halls_collection.find_one({'_id': b['hallId']})
        b['hall'] = hall
    return jsonify(user_bookings)

@bookings_bp.route('/all', methods=['GET'])
@auth_required
@admin_required
def get_all_bookings():
    all_bookings = list(bookings_collection.find({}))
    _sweep_completed_status(all_bookings)
    all_bookings.sort(key=lambda b: b.get('createdAt', ''), reverse=True)
    for b in all_bookings:
        hall = halls_collection.find_one({'_id': b['hallId']})
        user = users_collection.find_one({'_id': b['userId']})
        b['hall'] = hall
        b['user'] = {'name': user['name']} if user else None
    return jsonify(all_bookings)

@bookings_bp.route('/<id>/status', methods=['PUT'])
@auth_required
@admin_required
def update_booking_status(id):
    try:
        data = request.json
        status = data.get('status')
        booking = bookings_collection.find_one({'_id': id})
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404

        allowed_statuses = {'Approved', 'Rejected', 'Released'}
        if status not in allowed_statuses:
            return jsonify({'message': 'Invalid status update'}), 400

        if status == 'Released' and booking.get('status') != 'Approved':
            return jsonify({'message': 'Only approved bookings can be released'}), 400

        update_fields = {'status': status}
        unset_fields = {}

        if status == 'Approved':
            hall = halls_collection.find_one({'_id': booking['hallId']})
            user = users_collection.find_one({'_id': booking['userId']})
            qr_data = json.dumps({
                'bookingId': booking['_id'],
                'hall': hall['name'] if hall else 'Unknown',
                'user': user['name'] if user else 'Unknown',
                'date': booking['date'],
                'slot': f"{booking['startTime']} - {booking['endTime']}"
            })
            
            img = qrcode.make(qr_data)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            update_fields['qrCode'] = f"data:image/png;base64,{img_str}"
        else:
            unset_fields['qrCode'] = ""

        if status == 'Released':
            update_fields['releasedAt'] = datetime.datetime.now().isoformat()
            update_fields['releasedBy'] = request.user['id']

        update_doc = {'$set': update_fields}
        if unset_fields:
            update_doc['$unset'] = unset_fields

        bookings_collection.update_one({'_id': id}, update_doc)

        # Notify booking owner about status change
        status_emoji = '✅' if status == 'Approved' else '❌' if status == 'Rejected' else '🔓'
        hall = halls_collection.find_one({'_id': booking['hallId']})
        hall_name = hall['name'] if hall else 'Unknown Hall'
        create_notification(
            booking['userId'],
            f'{status_emoji} Booking {status}',
            f'Your booking for "{booking.get("eventName", "Event")}" at {hall_name} has been {status.lower()}.',
            'booking',
            '/pages/bookings.html'
        )

        updated_booking = bookings_collection.find_one({'_id': id})
        return jsonify(updated_booking)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bookings_bp.route('/<id>/cancel', methods=['PUT'])
@auth_required
def cancel_booking(id):
    try:
        booking = bookings_collection.find_one({'_id': id})
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
            
        if booking['userId'] != request.user['id'] and request.user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized to cancel this booking'}), 403
            
        if booking['status'] in ['Completed', 'Rejected']:
            return jsonify({'message': f"Cannot cancel a {booking['status']} booking"}), 400
            
        bookings_collection.update_one({'_id': id}, {'$set': {'status': 'Cancelled'}})
        return jsonify({'message': 'Booking cancelled successfully'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bookings_bp.route('/recommendations', methods=['GET'])
@auth_required
def get_recommendations():
    capacity = request.args.get('capacity')
    resources = request.args.get('resources')
    
    filtered = list(halls_collection.find({}))
    if capacity:
        filtered = [h for h in filtered if h.get('capacity', 0) >= int(capacity)]
    
    if resources:
        res_list = resources.split(',')
        hall_scores = []
        for h in filtered:
            score = sum(1 for r in res_list if r in h.get('resources', []))
            hall_scores.append((h, score))
        hall_scores.sort(key=lambda x: x[1], reverse=True)
        filtered_halls = [x[0] for x in hall_scores if x[1] > 0]
        top_halls = [filtered_halls[i] for i in range(min(3, len(filtered_halls)))]
        return jsonify(top_halls)
    
    # If no resources filter, still apply the top 3 limit
    top_halls = [filtered[i] for i in range(min(3, len(filtered)))]
    return jsonify(top_halls)

@bookings_bp.route('/approved', methods=['GET'])
def get_approved_bookings():
    # Public endpoint for the global calendar so everyone can see busy slots
    approved_bookings = list(bookings_collection.find({'status': 'Approved'}))
    _sweep_completed_status(approved_bookings)
    approved_bookings = [b for b in approved_bookings if b.get('status') == 'Approved']
    
    calendar_data = []
    for b in approved_bookings:
        hall = halls_collection.find_one({'_id': b['hallId']})
        calendar_data.append({
            'bookingId': b['_id'],
            'hallId': b['hallId'],
            'date': b['date'],
            'startTime': b['startTime'],
            'endTime': b['endTime'],
            'eventName': b.get('eventName', 'Booked Event'),
            'club': b.get('club', 'None'),
            'hallName': hall['name'] if hall else 'Unknown Hall'
        })
    return jsonify(calendar_data)


@bookings_bp.route('/availability', methods=['GET'])
@auth_required
def get_hall_availability():
    """Return all occupied slots (Pending + Approved bookings AND maintenance windows)
    for a given hall on a given date so the frontend can warn users in real-time."""
    hall_id = request.args.get('hallId')
    date = request.args.get('date')
    if not hall_id or not date:
        return jsonify({'message': 'hallId and date are required'}), 400

    hall = halls_collection.find_one({'_id': hall_id})
    if not hall:
        return jsonify({'message': 'Hall not found'}), 404

    # 1. Bookings that are active on this date
    occupied_bookings = list(bookings_collection.find({
        'hallId': hall_id,
        'date': date,
        'status': {'$in': ['Pending', 'Approved']}
    }))

    # Filter out bookings whose end time has already passed
    now = datetime.datetime.now()
    slots = []
    for b in occupied_bookings:
        try:
            end_dt = datetime.datetime.strptime(f"{date} {b['endTime']}", '%Y-%m-%d %H:%M')
            if end_dt <= now:
                continue
        except Exception:
            pass
        slots.append({
            'type': 'booking',
            'eventName': b.get('eventName', 'Event'),
            'startTime': b['startTime'],
            'endTime': b['endTime'],
            'status': b['status']
        })

    # 2. Maintenance windows on this date
    for window in hall.get('maintenanceWindows', []):
        if window.get('date') == date:
            try:
                end_dt = datetime.datetime.strptime(f"{date} {window['endTime']}", '%Y-%m-%d %H:%M')
                if end_dt <= now:
                    continue
            except Exception:
                pass
            slots.append({
                'type': 'maintenance',
                'eventName': window.get('title', 'Maintenance'),
                'startTime': window.get('startTime'),
                'endTime': window.get('endTime'),
                'status': 'Blocked'
            })

    # Sort by start time
    slots.sort(key=lambda s: s.get('startTime', ''))

    return jsonify({
        'hallId': hall_id,
        'hallName': hall.get('name', 'Unknown'),
        'date': date,
        'slots': slots
    })
