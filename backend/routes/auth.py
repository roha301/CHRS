import jwt
import bcrypt
import datetime
import os
import requests as http_requests
from flask import Blueprint, request, jsonify
from db import users_collection
from dotenv import load_dotenv
from middleware import auth_required

load_dotenv()
JWT_SECRET = os.getenv('JWT_SECRET', 'supersecretkey_kkwagh_2026')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/google-client-id', methods=['GET'])
def get_google_client_id():
    return jsonify({'clientId': GOOGLE_CLIENT_ID})

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
            'role': role,
            'authProvider': 'local',
            'avatarUrl': '',
            'createdAt': datetime.datetime.utcnow().isoformat()
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
                'role': 'admin',
                'email': 'admin@kkwagh.edu.in'
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
            'email': user.get('email', ''),
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({
            'token': token,
            'user': {
                'id': user['_id'],
                'name': user['name'],
                'role': user['role'],
                'email': user.get('email', '')
            }
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# --- Google Sign-In ---
@auth_bp.route('/google', methods=['POST'])
def google_login():
    """Verify Google ID token and create/login user. Only @kkwagh.edu.in emails allowed."""
    try:
        id_token = request.json.get('idToken')
        if not id_token:
            return jsonify({'message': 'ID token is required'}), 400

        # Verify token with Google
        verify_url = f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
        resp = http_requests.get(verify_url, timeout=10)
        if resp.status_code != 200:
            return jsonify({'message': 'Invalid Google token'}), 401

        google_data = resp.json()
        email = google_data.get('email', '')
        name = google_data.get('name', '')
        picture = google_data.get('picture', '')
        email_verified = google_data.get('email_verified', 'false')

        if email_verified != 'true' and email_verified is not True:
            return jsonify({'message': 'Google email is not verified'}), 401

        if not email.endswith('@kkwagh.edu.in'):
            return jsonify({'message': 'Only @kkwagh.edu.in email addresses are allowed. Please sign in with your college Google account.'}), 403

        # Find or create user
        user = users_collection.find_one({'email': email})
        if not user:
            user = {
                '_id': str(int(datetime.datetime.now().timestamp() * 1000)),
                'name': name,
                'email': email,
                'password': '',  # No password for Google users
                'role': 'user',
                'crn': None,
                'authProvider': 'google',
                'avatarUrl': picture,
                'createdAt': datetime.datetime.utcnow().isoformat()
            }
            users_collection.insert_one(user)
        else:
            # Update avatar and name from Google if changed
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'avatarUrl': picture, 'name': name}}
            )
            user['avatarUrl'] = picture
            user['name'] = name

        token = jwt.encode({
            'id': user['_id'],
            'role': user['role'],
            'name': user['name'],
            'email': user['email'],
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({
            'token': token,
            'user': {
                'id': user['_id'],
                'name': user['name'],
                'role': user['role'],
                'email': user['email'],
                'avatarUrl': user.get('avatarUrl', '')
            }
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# --- Get Profile ---
@auth_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    try:
        user = users_collection.find_one({'_id': request.user['id']})
        if not user:
            # Fallback for admin_root
            return jsonify({
                'id': request.user['id'],
                'name': request.user.get('name', 'Admin'),
                'email': request.user.get('email', ''),
                'role': request.user.get('role', 'admin'),
                'crn': None,
                'authProvider': 'local',
                'avatarUrl': '',
                'createdAt': ''
            })

        return jsonify({
            'id': user['_id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'crn': user.get('crn'),
            'authProvider': user.get('authProvider', 'local'),
            'avatarUrl': user.get('avatarUrl', ''),
            'createdAt': user.get('createdAt', '')
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# --- Update Profile ---
@auth_bp.route('/profile', methods=['PUT'])
@auth_required
def update_profile():
    try:
        data = request.json
        update_fields = {}

        if data.get('name'):
            update_fields['name'] = data['name']
        if data.get('crn') is not None:
            update_fields['crn'] = data['crn']

        if not update_fields:
            return jsonify({'message': 'Nothing to update'}), 400

        users_collection.update_one(
            {'_id': request.user['id']},
            {'$set': update_fields}
        )
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# --- Change Password ---
@auth_bp.route('/password', methods=['PUT'])
@auth_required
def change_password():
    try:
        data = request.json
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')

        if not old_password or not new_password:
            return jsonify({'message': 'Both old and new password are required'}), 400

        user = users_collection.find_one({'_id': request.user['id']})
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user.get('authProvider') == 'google':
            return jsonify({'message': 'Cannot change password for Google-authenticated accounts. Use Google account settings instead.'}), 400

        if not bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'message': 'Current password is incorrect'}), 401

        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users_collection.update_one(
            {'_id': request.user['id']},
            {'$set': {'password': hashed}}
        )
        return jsonify({'message': 'Password changed successfully'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500
