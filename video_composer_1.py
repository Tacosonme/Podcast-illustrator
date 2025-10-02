import os
import json
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math

class VideoComposer:
    def __init__(self, job_dir: str):
        self.job_dir = job_dir
        self.output_dir = os.path.join(job_dir, 'output')
        self.temp_dir = os.path.join(job_dir, 'temp')
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Video settings
        self.video_width = 1920
        self.video_height = 1080
        self.fps = 30
        self.default_image_duration = 5.0  # seconds
    
    def update_status(self, status: str, progress: int, message: str = ""):
        """Update job status"""
        status_data = {
            'status': status,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        status_file = os.path.join(self.job_dir, 'status.json')
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def get_audio_file(self) -> str:
        """Find the original audio file"""
        for filename in os.listdir(self.job_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
                return os.path.join(self.job_dir, filename)
        raise FileNotFoundError("No audio file found in job directory")
    
    def load_transcript(self) -> Dict[str, Any]:
        """Load the full transcript"""
        transcript_file = os.path.join(self.job_dir, 'full_transcript.json')
        if not os.path.exists(transcript_file):
            raise FileNotFoundError("Transcript not found")
        
        with open(transcript_file, 'r') as f:
            return json.load(f)
    
    def load_visual_content(self) -> Dict[str, Any]:
        """Load the visual content manifest"""
        manifest_file = os.path.join(self.job_dir, 'content', 'visual_content_manifest.json')
        if not os.path.exists(manifest_file):
            return {'images': [], 'videos': []}
        
        with open(manifest_file, 'r') as f:
            return json.load(f)
    
    def create_timeline(self, visual_content: Dict[str, Any], transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a timeline of visual content synchronized with audio"""
        timeline = []
        total_duration = transcript.get('total_duration', 0)
        
        # Sort visual content by timestamp
        all_content = []
        
        # Add images
        for image in visual_content.get('images', []):
            all_content.append({
                'type': 'image',
                'path': image['path'],
                'timestamp': image.get('timestamp', 0),
                'relevance_score': image.get('relevance_score', 0.5),
                'description': image.get('description', ''),
                'duration': self.default_image_duration
            })
        
        # Add videos
        for video in visual_content.get('videos', []):
            all_content.append({
                'type': 'video',
                'path': video['path'],
                'timestamp': video.get('timestamp', 0),
                'relevance_score': video.get('relevance_score', 0.8),
                'description': video.get('description', ''),
                'duration': 3.0  # Assume 3 seconds for generated videos
            })
        
        # Sort by timestamp
        all_content.sort(key=lambda x: x['timestamp'])
        
        # Create timeline with non-overlapping segments
        current_time = 0
        for content in all_content:
            start_time = max(content['timestamp'], current_time)
            end_time = min(start_time + content['duration'], total_duration)
            
            if end_time > start_time:  # Valid segment
                timeline.append({
                    'type': content['type'],
                    'path': content['path'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'description': content['description'],
                    'relevance_score': content['relevance_score']
                })
                current_time = end_time
        
        # Fill gaps with default background or repeat high-relevance content
        timeline = self.fill_timeline_gaps(timeline, total_duration)
        
        return timeline
    
    def fill_timeline_gaps(self, timeline: List[Dict[str, Any]], total_duration: float) -> List[Dict[str, Any]]:
        """Fill gaps in timeline with background content"""
        if not timeline:
            return timeline
        
        filled_timeline = []
        current_time = 0
        
        for segment in timeline:
            # Fill gap before this segment
            if segment['start_time'] > current_time:
                gap_duration = segment['start_time'] - current_time
                
                # Use a default background or extend previous content
                if filled_timeline:
                    # Extend the last segment
                    last_segment = filled_timeline[-1].copy()
                    last_segment['start_time'] = current_time
                    last_segment['end_time'] = segment['start_time']
                    last_segment['duration'] = gap_duration
                    filled_timeline.append(last_segment)
                else:
                    # Create a default background segment
                    filled_timeline.append({
                        'type': 'background',
                        'path': None,
                        'start_time': current_time,
                        'end_time': segment['start_time'],
                        'duration': gap_duration,
                        'description': 'Background',
                        'relevance_score': 0.1
                    })
            
            filled_timeline.append(segment)
            current_time = segment['end_time']
        
        # Fill remaining time if needed
        if current_time < total_duration:
            remaining_duration = total_duration - current_time
            if filled_timeline:
                last_segment = filled_timeline[-1].copy()
                last_segment['start_time'] = current_time
                last_segment['end_time'] = total_duration
                last_segment['duration'] = remaining_duration
                filled_timeline.append(last_segment)
        
        return filled_timeline
    
    def prepare_image_for_video(self, image_path: str, duration: float) -> str:
        """Convert image to video segment with specified duration"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(self.temp_dir, f"{base_name}_video.mp4")
        
        try:
            # Use ffmpeg to create video from image
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-loop', '1',  # Loop the image
                '-i', image_path,
                '-c:v', 'libx264',
                '-t', str(duration),  # Duration
                '-pix_fmt', 'yuv420p',
                '-vf', f'scale={self.video_width}:{self.video_height}:force_original_aspect_ratio=decrease,pad={self.video_width}:{self.video_height}:(ow-iw)/2:(oh-ih)/2:black',
                '-r', str(self.fps),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to convert image to video: {e.stderr}")
    
    def create_background_video(self, duration: float) -> str:
        """Create a default background video for gaps"""
        output_path = os.path.join(self.temp_dir, f"background_{int(duration)}.mp4")
        
        try:
            # Create a simple colored background
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'color=c=black:size={self.video_width}x{self.video_height}:duration={duration}:rate={self.fps}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to create background video: {e.stderr}")
    
    def prepare_video_segments(self, timeline: List[Dict[str, Any]]) -> List[str]:
        """Prepare all video segments according to timeline"""
        video_segments = []
        total_segments = len(timeline)
        
        for i, segment in enumerate(timeline):
            progress = 98 + (i / total_segments) * 1  # 98-99% progress
            self.update_status('rendering', int(progress), f'Preparing segment {i+1}/{total_segments}')
            
            if segment['type'] == 'image':
                # Convert image to video
                video_path = self.prepare_image_for_video(segment['path'], segment['duration'])
                video_segments.append(video_path)
                
            elif segment['type'] == 'video':
                # Use video directly (might need to resize/adjust)
                video_segments.append(segment['path'])
                
            elif segment['type'] == 'background':
                # Create background video
                video_path = self.create_background_video(segment['duration'])
                video_segments.append(video_path)
        
        return video_segments
    
    def concatenate_videos(self, video_segments: List[str], output_path: str) -> str:
        """Concatenate video segments into final video"""
        if not video_segments:
            raise ValueError("No video segments to concatenate")
        
        # Create concat file
        concat_file = os.path.join(self.temp_dir, 'concat_list.txt')
        with open(concat_file, 'w') as f:
            for segment in video_segments:
                f.write(f"file '{segment}'\\n")
        
        try:
            # Concatenate videos
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to concatenate videos: {e.stderr}")
    
    def add_audio_to_video(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Add audio track to video"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,  # Video input
                '-i', audio_path,  # Audio input
                '-c:v', 'copy',    # Copy video stream
                '-c:a', 'aac',     # Encode audio as AAC
                '-map', '0:v:0',   # Map video from first input
                '-map', '1:a:0',   # Map audio from second input
                '-shortest',       # End when shortest stream ends
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to add audio to video: {e.stderr}")
    
    def compose_video(self, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main video composition pipeline"""
        try:
            options = options or {}
            
            self.update_status('composing', 95, 'Starting video composition...')
            
            # Load required data
            transcript = self.load_transcript()
            visual_content = self.load_visual_content()
            audio_file = self.get_audio_file()
            
            if not visual_content.get('images') and not visual_content.get('videos'):
                raise Exception("No visual content available for video composition")
            
            # Create timeline
            self.update_status('composing', 96, 'Creating video timeline...')
            timeline = self.create_timeline(visual_content, transcript)
            
            # Prepare video segments
            self.update_status('composing', 97, 'Preparing video segments...')
            video_segments = self.prepare_video_segments(timeline)
            
            # Concatenate video segments
            self.update_status('composing', 98, 'Combining video segments...')
            video_only_path = os.path.join(self.temp_dir, 'video_only.mp4')
            self.concatenate_videos(video_segments, video_only_path)
            
            # Add audio to video
            self.update_status('composing', 99, 'Adding audio track...')
            final_output_path = os.path.join(self.output_dir, 'illustrated_podcast.mp4')
            self.add_audio_to_video(video_only_path, audio_file, final_output_path)
            
            # Get final video info
            file_size = os.path.getsize(final_output_path)
            
            # Save composition info
            composition_info = {
                'output_path': final_output_path,
                'file_size': file_size,
                'timeline_segments': len(timeline),
                'total_duration': transcript.get('total_duration', 0),
                'video_resolution': f"{self.video_width}x{self.video_height}",
                'fps': self.fps,
                'composition_timestamp': datetime.now().isoformat()
            }
            
            info_file = os.path.join(self.output_dir, 'composition_info.json')
            with open(info_file, 'w') as f:
                json.dump(composition_info, f, indent=2)
            
            self.update_status('completed', 100, 'Video composition completed successfully')
            
            return composition_info
            
        except Exception as e:
            self.update_status('failed', 0, f'Video composition failed: {str(e)}')
            raise e
    
    def get_composition_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the composed video"""
        info_file = os.path.join(self.output_dir, 'composition_info.json')
        if not os.path.exists(info_file):
            return None
        
        with open(info_file, 'r') as f:
            return json.load(f)
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")

