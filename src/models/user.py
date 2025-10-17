from src.config import supabase
from datetime import datetime

class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.username = kwargs.get('username', '')
        self.email = kwargs.get('email', '')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @classmethod
    def get_all(cls):
        """Get all users"""
        result = supabase.table('users').select('*').order('created_at', desc=True).execute()
        return [cls(**user) for user in result.data]
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID"""
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        if result.data:
            return cls(**result.data[0])
        return None
    
    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        result = supabase.table('users').select('*').eq('username', username).execute()
        if result.data:
            return cls(**result.data[0])
        return None
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        result = supabase.table('users').select('*').eq('email', email).execute()
        if result.data:
            return cls(**result.data[0])
        return None
    
    def save(self):
        """Save user to database"""
        data = {
            'username': self.username,
            'email': self.email,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if self.id:
            # Update existing user
            result = supabase.table('users').update(data).eq('id', self.id).execute()
            if result.data:
                updated_user = self.__class__(**result.data[0])
                self.__dict__.update(updated_user.__dict__)
                return self
        else:
            # Create new user
            result = supabase.table('users').insert(data).execute()
            if result.data:
                new_user = self.__class__(**result.data[0])
                self.__dict__.update(new_user.__dict__)
                return self
        return None
    
    def delete(self):
        """Delete user from database"""
        if self.id:
            supabase.table('users').delete().eq('id', self.id).execute()
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
