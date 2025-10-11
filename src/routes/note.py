from flask import Blueprint, jsonify, request
from src.models.note import Note, db
from src.llm import translate_text
from src.llm import extract_structured_notes, generate_notes_from_title

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    # Order primarily by manual 'order' field (desc), then by updated_at
    notes = Note.query.order_by(Note.order.desc(), Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        # Determine highest current order and set the new note to appear first
        max_order = db.session.query(db.func.max(Note.order)).scalar() or 0
        tags = data.get('tags')
        try:
            tags_json = __import__('json').dumps(tags) if tags is not None else None
        except Exception:
            tags_json = None
        event_date = data.get('event_date')
        event_time = data.get('event_time')
        note = Note(title=data['title'], content=data['content'], order=(max_order + 1), tags=tags_json, event_date=event_date, event_time=event_time)
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        tags = data.get('tags')
        if tags is not None:
            try:
                note.tags = __import__('json').dumps(tags)
            except Exception:
                note.tags = None
        # event date/time
        note.event_date = data.get('event_date', note.event_date)
        note.event_time = data.get('event_time', note.event_time)
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/reorder', methods=['POST'])
def reorder_notes():
    """Persist a new ordering for notes.

    Expected JSON body: { "order": [id1, id2, id3, ...] }
    The first id in the array will be given the highest order value so
    items display in that sequence when ordered by Note.order desc.
    """
    try:
        data = request.json
        if not data or 'order' not in data or not isinstance(data['order'], list):
            return jsonify({'error': 'Invalid payload, expected {"order": [ids...]}'}), 400

        ids = data['order']

        # Assign descending order values starting from len(ids) to 1
        total = len(ids)
        notes = {n.id: n for n in Note.query.filter(Note.id.in_(ids)).all()}

        for idx, note_id in enumerate(ids):
            note = notes.get(note_id)
            if note:
                # higher index -> lower priority, so invert
                note.order = total - idx

        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/<int:note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate a specific note's content using LLM helper.

    Expected JSON body: { "target_language": "French" }
    Returns the translated content but does not overwrite the original content.
    """
    note = Note.query.get_or_404(note_id)
    data = request.json or {}
    target = data.get('target_language', 'French')
    try:
        translated_title = translate_text(note.title or '', target_language=target)
        translated_content = translate_text(note.content or '', target_language=target)
        return jsonify({'translated_title': translated_title, 'translated': translated_content}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/<int:note_id>/generate-tags', methods=['POST'])
def generate_tags(note_id):
    """Generate tags for a note using LLM and persist them.

    Optional JSON body: { "lang": "English" }
    """
    note = Note.query.get_or_404(note_id)
    data = request.json or {}
    lang = data.get('lang', 'English')
    try:
        structured = extract_structured_notes(note.content or note.title or '', lang=lang)
        tags = structured.get('Tags') or structured.get('tags') or []
        if tags:
            note.tags = __import__('json').dumps(tags)
            db.session.commit()
        return jsonify({'tags': tags}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/generate', methods=['POST'])
def generate_note():
    """Generate a structured note from free-text using LLM and save it.

    Expected JSON body: { "text": "...", "lang": "English" }
    Returns the created note JSON.
    """
    try:
        data = request.json or {}
        title = data.get('title', '').strip()
        lang = data.get('lang', 'English')
        if title:
            # Generate content from a short title
            content = generate_notes_from_title(title, lang=lang)
        else:
            text = data.get('text', '').strip()
            if not text:
                return jsonify({'error': 'No title or text provided'}), 400
            structured = extract_structured_notes(text, lang=lang)
            # structured expected to contain Title and Notes
            title = structured.get('Title') or (text[:50] + '...')
            content = structured.get('Notes') or text

        # Determine highest current order and set the new note to appear first
        max_order = db.session.query(db.func.max(Note.order)).scalar() or 0
        note = Note(title=title, content=content, order=(max_order + 1))
        db.session.add(note)
        db.session.commit()

        # Attempt to generate tags using extract_structured_notes on the generated content
        try:
            structured = extract_structured_notes(content, lang=lang)
            tags = structured.get('Tags') or structured.get('tags') or []
            if tags:
                note.tags = __import__('json').dumps(tags)
                db.session.commit()
        except Exception:
            # ignore tag generation errors
            pass

        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])

