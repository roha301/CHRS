from flask import Blueprint, jsonify
from db import bookings_collection, halls_collection
from middleware import auth_required, admin_required
import datetime

analytics_bp = Blueprint('analytics', __name__)

APPROVAL_HISTORY_STATUSES = {'Approved', 'Completed', 'Released'}


def _sweep_completed_status(bookings):
    now = datetime.datetime.now()
    for booking in bookings:
        if booking.get('status') != 'Approved':
            continue
        try:
            end_dt = datetime.datetime.strptime(
                f"{booking['date']} {booking['endTime']}",
                '%Y-%m-%d %H:%M'
            )
        except Exception:
            continue

        if now > end_dt:
            booking['status'] = 'Completed'
            bookings_collection.update_one(
                {'_id': booking['_id']},
                {'$set': {'status': 'Completed'}}
            )


def _booking_created_date(booking):
    created_at = booking.get('createdAt')
    if created_at:
        try:
            return datetime.datetime.fromisoformat(created_at).date()
        except ValueError:
            pass

    try:
        return datetime.date.fromisoformat(booking.get('date', ''))
    except ValueError:
        return None


@analytics_bp.route('/stats', methods=['GET'])
@auth_required
@admin_required
def get_stats():
    all_bookings = list(bookings_collection.find({}))
    _sweep_completed_status(all_bookings)

    total_bookings = len(all_bookings)
    status_counts = {
        'Pending': 0,
        'Approved': 0,
        'Completed': 0,
        'Rejected': 0,
        'Cancelled': 0,
        'Released': 0
    }

    for booking in all_bookings:
        status = booking.get('status', 'Pending')
        status_counts[status] = status_counts.get(status, 0) + 1

    approval_history = [
        booking for booking in all_bookings
        if booking.get('status') in APPROVAL_HISTORY_STATUSES
    ]
    approved_count = len(approval_history)
    active_approved = [
        booking for booking in all_bookings
        if booking.get('status') == 'Approved'
    ]
    active_booked_halls = len({booking.get('hallId') for booking in active_approved})

    hall_counts = {}
    for booking in approval_history:
        hall_id = booking.get('hallId')
        if hall_id:
            hall_counts[hall_id] = hall_counts.get(hall_id, 0) + 1

    top_hall_id = None
    max_count = -1
    for hall_id, count in hall_counts.items():
        if count > max_count:
            max_count = count
            top_hall_id = hall_id

    top_hall = halls_collection.find_one({'_id': top_hall_id}) if top_hall_id else None

    time_counts = {}
    for booking in approval_history:
        start_time = booking.get('startTime', '')
        if ':' not in start_time:
            continue
        hour = start_time.split(':', 1)[0]
        time_counts[hour] = time_counts.get(hour, 0) + 1

    peak_times = sorted(time_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    peak_times_formatted = [f"{hour}:00" for hour, _ in peak_times]

    today = datetime.date.today()
    trends = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_total = 0
        day_approved = 0
        for booking in all_bookings:
            created_date = _booking_created_date(booking)
            if created_date != day:
                continue
            day_total += 1
            if booking.get('status') in APPROVAL_HISTORY_STATUSES:
                day_approved += 1

        trends.append({
            '_id': i,
            'date': day.isoformat(),
            'label': day.strftime('%d %b'),
            'count': day_total,
            'approvedCount': day_approved
        })

    approval_rate = round((approved_count / total_bookings) * 100, 1) if total_bookings else 0

    return jsonify({
        'totalBookings': total_bookings,
        'approvedBookings': approved_count,
        'activeApprovedBookings': len(active_approved),
        'activeBookedHalls': active_booked_halls,
        'pendingBookings': status_counts.get('Pending', 0),
        'approvalRate': approval_rate,
        'statusCounts': status_counts,
        'topHall': top_hall['name'] if top_hall else 'N/A',
        'peakTimes': peak_times_formatted,
        'trends': trends
    })
