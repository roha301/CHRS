import datetime
from flask import Blueprint, request, jsonify
from db import halls_collection
from middleware import auth_required, admin_required

halls_bp = Blueprint('halls', __name__)

@halls_bp.route('', methods=['GET'])
def get_all_halls():
    halls = list(halls_collection.find({}))
    return jsonify(halls)

@halls_bp.route('/<id>', methods=['GET'])
def get_hall_by_id(id):
    hall = halls_collection.find_one({'_id': id})
    if not hall:
        return jsonify({'message': 'Hall not found'}), 404
    return jsonify(hall)

@halls_bp.route('', methods=['POST'])
@auth_required
@admin_required
def create_hall():
    data = request.json
    hall = {**data, '_id': str(int(datetime.datetime.now().timestamp() * 1000))}
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
    halls_collection.update_one({'_id': id}, {'$set': update_data})
    
    updated_hall = halls_collection.find_one({'_id': id})
    return jsonify(updated_hall)

@halls_bp.route('/<id>', methods=['DELETE'])
@auth_required
@admin_required
def delete_hall(id):
    res = halls_collection.delete_one({'_id': id})
    if res.deleted_count > 0:
        return jsonify({'message': 'Hall deleted'})
    return jsonify({'message': 'Hall not found'}), 404
