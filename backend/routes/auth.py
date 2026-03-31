import jwt
import bcrypt
import datetime
import os
from flask import Blueprint, request, jsonify
from db import users_collection
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv('JWT_SECRET', 'supersecretkey_kkwagh_2026')

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        crn = data.get('crn')

        if not email or (role == 'user' and not email.endswith('@kkwagh.edu.in')):
            return jsonify({'message': 'Students must use @kkwagh.edu.in email domain. If admin, check credentials.'}), 400

        if users_collection.find_one({'email': email}):
            return jsonify({'message': 'User already exists'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = {
            '_id': str(int(datetime.datetime.now().timestamp() * 1000)),
            'crn': crn if role == 'user' else None,
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role
        }
        users_collection.insert_one(user)

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        expected_role = data.get('role', 'user')

        if expected_role == 'admin' and email == 'CHRS21' and password == 'KKWIEER':
            user = {
                '_id': 'admin_root',
                'name': 'System Administrator',
                'role': 'admin'
            }
        else:
            user = users_collection.find_one({'email': email})
            
            if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({'message': 'Invalid credentials'}), 401
                
            if user['role'] != expected_role:
                return jsonify({'message': f'Please login using the {user["role"].title()} portal'}), 401

        token = jwt.encode({
            'id': user['_id'],
            'role': user['role'],
            'name': user['name'],
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({
            'token': token,
            'user': {
                'id': user['_id'],
                'name': user['name'],
                'role': user['role']
            }
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500
