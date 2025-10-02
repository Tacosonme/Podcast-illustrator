import os
from flask import Blueprint, request, jsonify, current_app
from src.services.content_analyzer import ContentAnalyzer
from src.services.visual_content_generator import VisualContentGenerator

visual_bp = Blueprint('visual', __name__)

@visual_bp.route('/analyze/<job_id>', methods=['POST'])
def analyze_content(job_id):
    """Analyze transcript content for visual opportunities"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Check if transcript exists
        transcript_file = os.path.join(job_dir, 'full_transcript.json')
        if not os.path.exists(transcript_file):
            return jsonify({'error': 'Transcript not found. Please process audio first.'}), 400
        
        # Initialize content analyzer
        analyzer = ContentAnalyzer(job_dir)
        
        # Perform content analysis
        analysis_result = analyzer.analyze_content()
        
        return jsonify({
            'job_id': job_id,
            'status': 'analyzed',
            'total_visual_moments': analysis_result['total_visual_moments'],
            'analysis_timestamp': analysis_result['analysis_timestamp']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visual_bp.route('/queries/<job_id>', methods=['GET'])
def get_visual_queries(job_id):
    """Get prioritized visual content queries for a job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Get query parameters
        max_queries = request.args.get('max_queries', 20, type=int)
        
        # Initialize content analyzer
        analyzer = ContentAnalyzer(job_dir)
        
        # Get search queries
        queries = analyzer.get_search_queries(max_queries=max_queries)
        
        return jsonify({
            'job_id': job_id,
            'queries': queries,
            'total_queries': len(queries)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visual_bp.route('/generate/<job_id>', methods=['POST'])
def generate_visual_content(job_id):
    """Generate visual content (images and videos) for a job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Get generation options
        options = request.get_json() or {}
        max_queries = options.get('max_queries', 15)
        generate_videos = options.get('generate_videos', False)
        
        # Initialize services
        analyzer = ContentAnalyzer(job_dir)
        generator = VisualContentGenerator(job_dir)
        
        # Get visual queries
        queries = analyzer.get_search_queries(max_queries=max_queries)
        
        # Filter queries based on options
        if not generate_videos:
            queries = [q for q in queries if q.get('type') != 'video']
        
        # Generate visual content
        result = generator.process_visual_content(queries)
        
        return jsonify({
            'job_id': job_id,
            'status': 'content_generated',
            'images_generated': len(result['images']),
            'videos_generated': len(result['videos']),
            'failed_queries': len(result['failed_queries']),
            'total_processed': len(queries)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visual_bp.route('/content/<job_id>', methods=['GET'])
def get_visual_content(job_id):
    """Get all generated visual content for a job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        generator = VisualContentGenerator(job_dir)
        
        # Load content manifest
        manifest_file = os.path.join(job_dir, 'content', 'visual_content_manifest.json')
        if not os.path.exists(manifest_file):
            return jsonify({'error': 'No visual content found'}), 404
        
        import json
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        # Add URLs to content items
        for image in manifest.get('images', []):
            image['url'] = f'/api/files/{job_id}/images/{image["filename"]}'
        
        for video in manifest.get('videos', []):
            video['url'] = f'/api/files/{job_id}/videos/{video["filename"]}'
        
        return jsonify(manifest), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visual_bp.route('/content/<job_id>/timeline', methods=['GET'])
def get_content_timeline(job_id):
    """Get visual content organized by timestamp"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Get timeline parameters
        start_time = request.args.get('start_time', 0, type=float)
        end_time = request.args.get('end_time', 999999, type=float)
        window = request.args.get('window', 30, type=float)
        
        generator = VisualContentGenerator(job_dir)
        
        # Load content manifest
        manifest_file = os.path.join(job_dir, 'content', 'visual_content_manifest.json')
        if not os.path.exists(manifest_file):
            return jsonify({'timeline': []}), 200
        
        import json
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        # Create timeline
        timeline = []
        
        # Process images
        for image in manifest.get('images', []):
            timestamp = image.get('timestamp', 0)
            if start_time <= timestamp <= end_time:
                timeline.append({
                    'timestamp': timestamp,
                    'type': 'image',
                    'filename': image['filename'],
                    'url': f'/api/files/{job_id}/images/{image["filename"]}',
                    'description': image.get('description', ''),
                    'query': image.get('query', ''),
                    'source': image.get('source', 'unknown'),
                    'relevance_score': image.get('relevance_score', 0.5)
                })
        
        # Process videos
        for video in manifest.get('videos', []):
            timestamp = video.get('timestamp', 0)
            if start_time <= timestamp <= end_time:
                timeline.append({
                    'timestamp': timestamp,
                    'type': 'video',
                    'filename': video['filename'],
                    'url': f'/api/files/{job_id}/videos/{video["filename"]}',
                    'description': video.get('description', ''),
                    'query': video.get('query', ''),
                    'source': 'generated',
                    'relevance_score': 0.8
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return jsonify({
            'job_id': job_id,
            'timeline': timeline,
            'total_items': len(timeline),
            'time_range': {'start': start_time, 'end': end_time}
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visual_bp.route('/preview/<job_id>', methods=['GET'])
def preview_content(job_id):
    """Get a preview of visual content for quick review"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Get preview parameters
        max_items = request.args.get('max_items', 10, type=int)
        
        generator = VisualContentGenerator(job_dir)
        
        # Load content manifest
        manifest_file = os.path.join(job_dir, 'content', 'visual_content_manifest.json')
        if not os.path.exists(manifest_file):
            return jsonify({'preview': []}), 200
        
        import json
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        # Create preview with highest relevance items
        preview_items = []
        
        # Add top images
        images = manifest.get('images', [])
        images.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        for image in images[:max_items//2]:
            preview_items.append({
                'type': 'image',
                'timestamp': image.get('timestamp', 0),
                'url': f'/api/files/{job_id}/images/{image["filename"]}',
                'description': image.get('description', ''),
                'relevance_score': image.get('relevance_score', 0.5)
            })
        
        # Add top videos
        videos = manifest.get('videos', [])
        for video in videos[:max_items//2]:
            preview_items.append({
                'type': 'video',
                'timestamp': video.get('timestamp', 0),
                'url': f'/api/files/{job_id}/videos/{video["filename"]}',
                'description': video.get('description', ''),
                'relevance_score': 0.8
            })
        
        # Sort by relevance
        preview_items.sort(key=lambda x: x['relevance_score'], reverse=True)
        preview_items = preview_items[:max_items]
        
        return jsonify({
            'job_id': job_id,
            'preview': preview_items,
            'total_available': len(images) + len(videos)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

