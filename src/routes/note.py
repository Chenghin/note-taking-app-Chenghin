from flask import Blueprint, jsonify, request
from src.models.note import Note
from src.llm import translate_text
from src.llm import extract_structured_notes, generate_notes_from_title
import json

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    try:
        notes = Note.get_all()
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        # Get max order for new note positioning
        max_order = Note.get_max_order()
        
        note = Note(
            title=data['title'],
            content=data['content'],
            order=max_order + 1,
            tags=data.get('tags'),
            event_date=data.get('event_date'),
            event_time=data.get('event_time')
        )
        
        saved_note = note.save()
        if saved_note:
            return jsonify(saved_note.to_dict()), 201
        else:
            return jsonify({'error': 'Failed to create note'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.get_by_id(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.get_by_id(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        tags = data.get('tags')
        if tags is not None:
            note.tags = tags
        # event date/time
        note.event_date = data.get('event_date', note.event_date)
        note.event_time = data.get('event_time', note.event_time)
        
        saved_note = note.save()
        if saved_note:
            return jsonify(saved_note.to_dict())
        else:
            return jsonify({'error': 'Failed to update note'}), 500
    except Exception as e:
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
        
        # Create list of (id, order) pairs for bulk update
        id_order_pairs = []
        for idx, note_id in enumerate(ids):
            # higher index -> lower priority, so invert
            order_value = total - idx
            id_order_pairs.append((note_id, order_value))
        
        # Bulk update orders
        Note.update_orders(id_order_pairs)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/<int:note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate a specific note's content using LLM helper.

    Expected JSON body: { "target_language": "French" }
    Returns the translated content but does not overwrite the original content.
    """
    note = Note.get_by_id(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    
    data = request.json or {}
    target = data.get('target_language', 'French')
    try:
        # Check if content is already in target language
        if not _needs_translation(note.title or '', note.content or '', note.tags or '', target):
            return jsonify({'no_translation_needed': True}), 200
            
        translated_title = translate_text(note.title or '', target_language=target)
        translated_content = translate_text(note.content or '', target_language=target)
        
        # Translate tags if they exist, extracting only literal words from stored format
        translated_tags = ''
        if note.tags:
            from src.llm import translate_tags
            # translate_tags will accept list or JSON/string and return cleaned CSV
            translated_tags = translate_tags(note.tags, target_language=target)
        
        return jsonify({
            'translated_title': translated_title, 
            'translated': translated_content,
            'translated_tags': translated_tags
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _needs_translation(title, content, tags, target_language):
    """Check if the content needs translation by detecting if it's already in the target language"""
    from src.llm import detect_language
    # Normalize tags into plain text (handle JSON string or list)
    tags_text = ''
    if tags:
        try:
            if isinstance(tags, str):
                import json
                parsed = json.loads(tags)
                if isinstance(parsed, list):
                    tags_text = ' '.join([str(t) for t in parsed])
                else:
                    tags_text = str(parsed)
            elif isinstance(tags, list):
                tags_text = ' '.join([str(t) for t in tags])
            else:
                tags_text = str(tags)
        except Exception:
            # fallback: treat tags as CSV or plain string
            if isinstance(tags, str):
                tags_text = ','.join([t.strip() for t in tags.split(',') if t.strip()])
            else:
                tags_text = str(tags)

    # Combine all text for language detection
    combined_text = f"{title} {content} {tags_text}".strip()
    if not combined_text:
        return False
    
    try:
        detected_language = detect_language(combined_text)
        # Simple check - if detected language matches target, no translation needed
        return not (detected_language.lower() == target_language.lower())
    except:
        # If detection fails, assume translation is needed
        return True


@note_bp.route('/notes/<int:note_id>/generate-tags', methods=['POST'])
def generate_tags(note_id):
    """Generate tags for a note using LLM and persist them.

    Optional JSON body: { "lang": "English" }
    """
    note = Note.get_by_id(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    
    data = request.json or {}
    lang = data.get('lang', 'English')
    try:
        structured = extract_structured_notes(note.content or note.title or '', lang=lang)
        tags = structured.get('Tags') or structured.get('tags') or []
        if tags:
            note.tags = tags
            note.save()
        return jsonify({'tags': tags}), 200
    except Exception as e:
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
        max_order = Note.get_max_order()
        note = Note(title=title, content=content, order=max_order + 1)
        saved_note = note.save()
        
        if not saved_note:
            return jsonify({'error': 'Failed to create note'}), 500

        # Attempt to generate tags using extract_structured_notes on the generated content
        try:
            structured = extract_structured_notes(content, lang=lang)
            tags = structured.get('Tags') or structured.get('tags') or []
            if tags:
                saved_note.tags = tags
                saved_note.save()
        except Exception:
            # ignore tag generation errors
            pass

        return jsonify(saved_note.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.get_by_id(note_id)
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        success = note.delete()
        if success:
            return '', 204
        else:
            return jsonify({'error': 'Failed to delete note'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    try:
        notes = Note.search(query)
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

