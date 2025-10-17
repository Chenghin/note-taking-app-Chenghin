from flask import Blueprint, jsonify, request
from src.models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    try:
        users = User.get_all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        if not data or 'username' not in data or 'email' not in data:
            return jsonify({'error': 'Username and email are required'}), 400
        
        user = User(username=data['username'], email=data['email'])
        saved_user = user.save()
        if saved_user:
            return jsonify(saved_user.to_dict()), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        
        saved_user = user.save()
        if saved_user:
            return jsonify(saved_user.to_dict())
        else:
            return jsonify({'error': 'Failed to update user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        success = user.delete()
        if success:
            return '', 204
        else:
            return jsonify({'error': 'Failed to delete user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
