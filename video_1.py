import os
from flask import Blueprint, request, jsonify, current_app, send_file
from src.services.video_composer import VideoComposer

video_bp = Blueprint('video', __name__)

@video_bp.route('/compose/<job_id>', methods=['POST'])
def compose_video(job_id):
    """Start video composition for a job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Check prerequisites
        transcript_file = os.path.join(job_dir, 'full_transcript.json')
        if not os.path.exists(transcript_file):
            return jsonify({'error': 'Transcript not found. Please process audio first.'}), 400
        
        visual_manifest = os.path.join(job_dir, 'content', 'visual_content_manifest.json')
        if not os.path.exists(visual_manifest):
            return jsonify({'error': 'Visual content not found. Please generate visual content first.'}), 400
        
        # Get composition options
        options = request.get_json() or {}
        
        # Initialize video composer
        composer = VideoComposer(job_dir)
        
        # Start composition
        composition_info = composer.compose_video(options)
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'output_path': composition_info['output_path'],
            'file_size': composition_info['file_size'],
            'timeline_segments': composition_info['timeline_segments'],
            'total_duration': composition_info['total_duration'],
            'download_url': f'/api/download/{job_id}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/info/<job_id>', methods=['GET'])
def get_composition_info(job_id):
    """Get information about a composed video"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        composer = VideoComposer(job_dir)
        composition_info = composer.get_composition_info()
        
        if not composition_info:
            return jsonify({'error': 'No composed video found'}), 404
        
        # Add download URL
        composition_info['download_url'] = f'/api/download/{job_id}'
        
        return jsonify(composition_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/download/<job_id>', methods=['GET'])
def download_video(job_id):
    """Download the composed video"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Find the output video file
        output_dir = os.path.join(job_dir, 'output')
        video_file = os.path.join(output_dir, 'illustrated_podcast.mp4')
        
        if not os.path.exists(video_file):
            return jsonify({'error': 'Video not found. Please compose video first.'}), 404
        
        # Send file for download
        return send_file(
            video_file,
            as_attachment=True,
            download_name=f'illustrated_podcast_{job_id}.mp4',
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/preview/<job_id>', methods=['GET'])
def preview_video(job_id):
    """Stream video for preview (without download)"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Find the output video file
        output_dir = os.path.join(job_dir, 'output')
        video_file = os.path.join(output_dir, 'illustrated_podcast.mp4')
        
        if not os.path.exists(video_file):
            return jsonify({'error': 'Video not found. Please compose video first.'}), 404
        
        # Stream file for preview
        return send_file(
            video_file,
            as_attachment=False,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/timeline/<job_id>', methods=['GET'])
def get_video_timeline(job_id):
    """Get the video composition timeline"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        composer = VideoComposer(job_dir)
        
        # Load required data to recreate timeline
        transcript = composer.load_transcript()
        visual_content = composer.load_visual_content()
        
        if not visual_content.get('images') and not visual_content.get('videos'):
            return jsonify({'timeline': []}), 200
        
        # Create timeline
        timeline = composer.create_timeline(visual_content, transcript)
        
        # Format timeline for response
        formatted_timeline = []
        for segment in timeline:
            formatted_timeline.append({
                'type': segment['type'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['duration'],
                'description': segment['description'],
                'relevance_score': segment['relevance_score']
            })
        
        return jsonify({
            'job_id': job_id,
            'timeline': formatted_timeline,
            'total_segments': len(formatted_timeline),
            'total_duration': transcript.get('total_duration', 0)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/cleanup/<job_id>', methods=['POST'])
def cleanup_temp_files(job_id):
    """Clean up temporary files for a job"""
    try:
        job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        composer = VideoComposer(job_dir)
        composer.cleanup_temp_files()
        
        return jsonify({
            'job_id': job_id,
            'status': 'cleaned',
            'message': 'Temporary files cleaned up successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all available jobs"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            return jsonify({'jobs': []}), 200
        
        jobs = []
        for job_id in os.listdir(upload_folder):
            job_dir = os.path.join(upload_folder, job_id)
            if os.path.isdir(job_dir):
                # Get job status
                status_file = os.path.join(job_dir, 'status.json')
                status_info = {'status': 'unknown', 'progress': 0}
                
                if os.path.exists(status_file):
                    try:
                        import json
                        with open(status_file, 'r') as f:
                            status_info = json.load(f)
                    except:
                        pass
                
                # Check if video is available
                video_file = os.path.join(job_dir, 'output', 'illustrated_podcast.mp4')
                has_video = os.path.exists(video_file)
                
                jobs.append({
                    'job_id': job_id,
                    'status': status_info.get('status', 'unknown'),
                    'progress': status_info.get('progress', 0),
                    'has_video': has_video,
                    'last_updated': status_info.get('timestamp', '')
                })
        
        # Sort by last updated (most recent first)
        jobs.sort(key=lambda x: x['last_updated'], reverse=True)
        
        return jsonify({
            'jobs': jobs,
            'total_jobs': len(jobs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

