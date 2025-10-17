from src.config import supabase
from datetime import datetime
import json

class Note:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.title = kwargs.get('title', '')
        self.content = kwargs.get('content', '')
        self.order = kwargs.get('order', 0)
        self.tags = kwargs.get('tags')
        self.event_date = kwargs.get('event_date')
        self.event_time = kwargs.get('event_time')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    def __repr__(self):
        return f'<Note {self.title}>'
    
    @classmethod
    def get_all(cls):
        """Get all notes ordered by order desc, then updated_at desc"""
        result = supabase.table('notes').select('*').order('order', desc=True).order('updated_at', desc=True).execute()
        return [cls(**note) for note in result.data]
    
    @classmethod
    def get_by_id(cls, note_id):
        """Get note by ID"""
        result = supabase.table('notes').select('*').eq('id', note_id).execute()
        if result.data:
            return cls(**result.data[0])
        return None
    
    @classmethod
    def search(cls, query):
        """Search notes by title or content"""
        # Using ilike for case-insensitive search
        result = supabase.table('notes').select('*').or_(f'title.ilike.%{query}%,content.ilike.%{query}%').order('updated_at', desc=True).execute()
        return [cls(**note) for note in result.data]
    
    @classmethod
    def get_max_order(cls):
        """Get the maximum order value"""
        result = supabase.table('notes').select('order').order('order', desc=True).limit(1).execute()
        if result.data:
            return result.data[0]['order']
        return 0
    
    def save(self):
        """Save note to database"""
        data = {
            'title': self.title,
            'content': self.content,
            'order': self.order,
            'tags': json.dumps(self.tags) if self.tags is not None else None,
            'event_date': self.event_date,
            'event_time': self.event_time,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if self.id:
            # Update existing note
            result = supabase.table('notes').update(data).eq('id', self.id).execute()
            if result.data:
                updated_note = self.__class__(**result.data[0])
                self.__dict__.update(updated_note.__dict__)
                return self
        else:
            # Create new note
            result = supabase.table('notes').insert(data).execute()
            if result.data:
                new_note = self.__class__(**result.data[0])
                self.__dict__.update(new_note.__dict__)
                return self
        return None
    
    def delete(self):
        """Delete note from database"""
        if self.id:
            supabase.table('notes').delete().eq('id', self.id).execute()
            return True
        return False
    
    @classmethod
    def update_orders(cls, id_order_pairs):
        """Bulk update note orders"""
        for note_id, order_value in id_order_pairs:
            supabase.table('notes').update({'order': order_value}).eq('id', note_id).execute()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'order': self.order,
            'tags': [] if not self.tags else (json.loads(self.tags) if isinstance(self.tags, str) else self.tags),
            'event_date': self.event_date,
            'event_time': self.event_time,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

