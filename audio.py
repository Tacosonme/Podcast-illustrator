import os
import uuid
import subprocess
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import openai
from src.services.audio_processor import AudioProcessor
from src.services.content_analyzer import ContentAnalyzer

audio_bp = Blueprint('audio', __name__)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@audio_bp.route('/upload', methods=['POST'])
def upload_audio():
    """Upload and validate audio file"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Supported: mp3, wav, m4a, flac, ogg'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create job directory
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(job_dir, filename)
        file.save(file_path)
        
        # Validate file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            os.rmdir(job_dir)
            return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
        
        # Get audio duration
        try:
            result = subprocess.run([
                'ffprobe', '-i', file_path, '-show_entries', 'format=duration',
                '-v', 'quiet', '-of', 'csv=p=0'
            ], capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            duration = 0
        
        return jsonify({
            'job_id': job_id,
            'filename': filename,
            'file_size': file_size,
            'duration': duration,
            'status': 'uploaded'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@audio_bp.route('/process/<job_id>', methods=['POST'])
def process_audio(job_id):
    """Start audio processing pipeline"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Get processing options
        options = request.get_json() or {}
        segment_duration = options.get('segment_duration', 600)  # 10 minutes default
        generate_images = options.get('generate_images', True)
        generate_videos = options.get('generate_videos', False)
        
        # Initialize audio processor
        processor = AudioProcessor(job_dir)
        
        # Start processing (this would typically be done with Celery in production)
        result = processor.process_audio(
            segment_duration=segment_duration,
            generate_images=generate_images,
            generate_videos=generate_videos
        )
        
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'segments_created': result.get('segments_created', 0),
            'estimated_time': result.get('estimated_time', 0)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@audio_bp.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get processing status for a job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        status_file = os.path.join(job_dir, 'status.json')
        if os.path.exists(status_file):
            import json
            with open(status_file, 'r') as f:
                status = json.load(f)
            return jsonify(status), 200
        else:
            return jsonify({
                'job_id': job_id,
                'status': 'uploaded',
                'progress': 0
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@audio_bp.route('/transcript/<job_id>', methods=['GET'])
def get_transcript(job_id):
    """Get transcript for a processed job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        transcript_file = os.path.join(job_dir, 'full_transcript.json')
        
        if not os.path.exists(transcript_file):
            return jsonify({'error': 'Transcript not found'}), 404
        
        import json
        with open(transcript_file, 'r') as f:
            transcript = json.load(f)
        
        return jsonify(transcript), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@audio_bp.route('/images/<job_id>', methods=['GET'])
def get_images(job_id):
    """Get generated images for a job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        images_dir = os.path.join(job_dir, 'images')
        
        if not os.path.exists(images_dir):
            return jsonify({'images': []}), 200
        
        images = []
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append({
                    'filename': filename,
                    'url': f'/api/files/{job_id}/images/{filename}',
                    'timestamp': filename.split('_')[0] if '_' in filename else '0'
                })
        
        return jsonify({'images': images}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@audio_bp.route('/files/<job_id>/<path:filepath>', methods=['GET'])
def get_file(job_id, filepath):
    """Serve files from job directory"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        file_path = os.path.join(job_dir, filepath)
        
        if not os.path.exists(file_path) or not file_path.startswith(job_dir):
            return jsonify({'error': 'File not found'}), 404
        
        from flask import send_file
        return send_file(file_path)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

