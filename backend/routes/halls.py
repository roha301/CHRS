import datetime
from flask import Blueprint, request, jsonify
from db import halls_collection, bookings_collection
from middleware import auth_required, admin_required

halls_bp = Blueprint('halls', __name__)


def _parse_minutes(value):
    try:
        hour, minute = map(int, str(value).split(':'))
        return (hour * 60) + minute
    except Exception:
        return None


def _windows_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and end_a > start_b


def _normalize_hall(hall):
    if not hall:
        return hall

    hall['resources'] = [item for item in hall.get('resources', []) if item]
    hall['maintenanceWindows'] = sorted(
        hall.get('maintenanceWindows', []),
        key=lambda item: (
            item.get('date', ''),
            item.get('startTime', ''),
            item.get('createdAt', '')
        )
    )
    return hall


def _serialize_maintenance_window(hall, window):
    return {
        'id': window.get('id'),
        'title': window.get('title') or 'Maintenance',
        'notes': window.get('notes', ''),
        'date': window.get('date', ''),
        'startTime': window.get('startTime', ''),
        'endTime': window.get('endTime', ''),
        'createdAt': window.get('createdAt', ''),
        'hallId': hall.get('_id'),
        'hallName': hall.get('name', 'Unknown Hall'),
        'entryType': 'maintenance',
        'eventName': window.get('title') or 'Maintenance',
        'club': 'Maintenance'
    }

@halls_bp.route('', methods=['GET'])
def get_all_halls():
    halls = [_normalize_hall(hall) for hall in halls_collection.find({})]
    return jsonify(halls)

@halls_bp.route('/maintenance', methods=['GET'])
def get_maintenance_windows():
    windows = []
    for hall in halls_collection.find({}, {'name': 1, 'maintenanceWindows': 1}):
        hall = _normalize_hall(hall)
        for window in hall.get('maintenanceWindows', []):
            windows.append(_serialize_maintenance_window(hall, window))

    windows.sort(key=lambda item: (item.get('date', ''), item.get('startTime', ''), item.get('hallName', '')))
    return jsonify(windows)

@halls_bp.route('/<id>', methods=['GET'])
def get_hall_by_id(id):
    hall = halls_collection.find_one({'_id': id})
    if not hall:
        return jsonify({'message': 'Hall not found'}), 404
    return jsonify(_normalize_hall(hall))

@halls_bp.route('', methods=['POST'])
@auth_required
@admin_required
def create_hall():
    data = request.json
    hall = {
        **data,
        '_id': str(int(datetime.datetime.now().timestamp() * 1000)),
        'resources': [item for item in data.get('resources', []) if item],
        'maintenanceWindows': []
    }
    halls_collection.insert_one(hall)
    return jsonify(hall), 201

@halls_bp.route('/<id>', methods=['PUT'])
@auth_required
@admin_required
def update_hall(id):
    hall = halls_collection.find_one({'_id': id})
    if not hall:
        return jsonify({'message': 'Hall not found'}), 404
    
    # Exclude _id from the update if present in request.json
    update_data = {k: v for k, v in request.json.items() if k != '_id'}
    if 'resources' in update_data:
        update_data['resources'] = [item for item in update_data.get('resources', []) if item]
    halls_collection.update_one({'_id': id}, {'$set': update_data})
    
    updated_hall = halls_collection.find_one({'_id': id})
    return jsonify(_normalize_hall(updated_hall))


@halls_bp.route('/<id>/maintenance', methods=['POST'])
@auth_required
@admin_required
def create_maintenance_window(id):
    hall = halls_collection.find_one({'_id': id})
    if not hall:
        return jsonify({'message': 'Hall not found'}), 404

    data = request.json or {}
    title = (data.get('title') or 'Maintenance').strip() or 'Maintenance'
    date = (data.get('date') or '').strip()
    start_time = (data.get('startTime') or '').strip()
    end_time = (data.get('endTime') or '').strip()
    notes = (data.get('notes') or '').strip()

    start_minutes = _parse_minutes(start_time)
    end_minutes = _parse_minutes(end_time)
    if not date or start_minutes is None or end_minutes is None:
        return jsonify({'message': 'Date, start time, and end time are required'}), 400
    if start_minutes >= end_minutes:
        return jsonify({'message': 'Maintenance end time must be after the start time'}), 400

    hall = _normalize_hall(hall)
    for window in hall.get('maintenanceWindows', []):
        if window.get('date') != date:
            continue
        window_start = _parse_minutes(window.get('startTime'))
        window_end = _parse_minutes(window.get('endTime'))
        if window_start is None or window_end is None:
            continue
        if _windows_overlap(start_minutes, end_minutes, window_start, window_end):
            return jsonify({'message': 'This maintenance block overlaps an existing maintenance window'}), 409

    conflicting_booking = bookings_collection.find_one({
        'hallId': id,
        'date': date,
        'status': {'$in': ['Pending', 'Approved']},
        'startTime': {'$lt': end_time},
        'endTime': {'$gt': start_time}
    })
    if conflicting_booking:
        return jsonify({
            'message': f'This maintenance window overlaps the booking "{conflicting_booking.get("eventName", "Event")}"'
        }), 409

    window = {
        'id': str(int(datetime.datetime.now().timestamp() * 1000000)),
        'title': title,
        'notes': notes,
        'date': date,
        'startTime': start_time,
        'endTime': end_time,
        'createdAt': datetime.datetime.utcnow().isoformat(),
        'createdBy': request.user['id']
    }
    halls_collection.update_one({'_id': id}, {'$push': {'maintenanceWindows': window}})
    return jsonify(_serialize_maintenance_window(hall, window)), 201


@halls_bp.route('/<id>/maintenance/<window_id>', methods=['DELETE'])
@auth_required
@admin_required
def delete_maintenance_window(id, window_id):
    hall = halls_collection.find_one({'_id': id})
    if not hall:
        return jsonify({'message': 'Hall not found'}), 404

    result = halls_collection.update_one(
        {'_id': id},
        {'$pull': {'maintenanceWindows': {'id': window_id}}}
    )

    if result.modified_count == 0:
        return jsonify({'message': 'Maintenance window not found'}), 404

    return jsonify({'message': 'Maintenance window removed'})

@halls_bp.route('/<id>', methods=['DELETE'])
@auth_required
@admin_required
def delete_hall(id):
    res = halls_collection.delete_one({'_id': id})
    if res.deleted_count > 0:
        return jsonify({'message': 'Hall deleted'})
    return jsonify({'message': 'Hall not found'}), 404
