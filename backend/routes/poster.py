from flask import Blueprint, jsonify
from db import bookings_collection, halls_collection, users_collection
from utils.poster import generate_poster
from middleware import auth_required

poster_bp = Blueprint('poster', __name__)

@poster_bp.route('/<id>/poster', methods=['GET'])
@auth_required
def get_booking_poster(id):
    booking = bookings_collection.find_one({'_id': id})
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404
    
    hall = halls_collection.find_one({'_id': booking['hallId']})
    user = users_collection.find_one({'_id': booking['userId']})
    
    if not hall or not user:
        return jsonify({'message': 'Internal data missing'}), 500
        
    poster_data = generate_poster(booking, hall, user)
    return jsonify({'poster': f"data:image/png;base64,{poster_data}"})
