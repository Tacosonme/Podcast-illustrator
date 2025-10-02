import os
import json
import subprocess
import tempfile
from typing import List, Dict, Any
import openai
from datetime import datetime

class AudioProcessor:
    def __init__(self, job_dir: str):
        self.job_dir = job_dir
        self.segments_dir = os.path.join(job_dir, 'segments')
        self.transcripts_dir = os.path.join(job_dir, 'transcripts')
        self.client = openai.OpenAI()
        
        # Create necessary directories
        os.makedirs(self.segments_dir, exist_ok=True)
        os.makedirs(self.transcripts_dir, exist_ok=True)
    
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
        """Find the uploaded audio file"""
        for filename in os.listdir(self.job_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
                return os.path.join(self.job_dir, filename)
        raise FileNotFoundError("No audio file found in job directory")
    
    def segment_audio(self, segment_duration: int = 600) -> List[str]:
        """Split audio into segments for transcription"""
        self.update_status('processing', 10, 'Segmenting audio file...')
        
        audio_file = self.get_audio_file()
        segment_files = []
        
        try:
            # Use ffmpeg to segment the audio with proper encoding
            cmd = [
                'ffmpeg', '-i', audio_file,
                '-f', 'segment',
                '-segment_time', str(segment_duration),
                '-c:a', 'libmp3lame',  # Use MP3 encoder instead of copy
                '-b:a', '128k',        # Set bitrate
                '-ar', '44100',        # Set sample rate
                '-ac', '2',            # Set to stereo
                os.path.join(self.segments_dir, 'segment_%03d.mp3')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Get list of created segments
            for filename in sorted(os.listdir(self.segments_dir)):
                if filename.startswith('segment_') and filename.endswith('.mp3'):
                    segment_files.append(os.path.join(self.segments_dir, filename))
            
            self.update_status('processing', 20, f'Created {len(segment_files)} audio segments')
            return segment_files
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Audio segmentation failed: {e.stderr}")
    
    def transcribe_segment(self, segment_file: str, segment_index: int) -> Dict[str, Any]:
        """Transcribe a single audio segment using OpenAI Whisper"""
        try:
            with open(segment_file, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Process the transcript data
            transcript_data = {
                'segment_index': segment_index,
                'text': transcript.text,
                'language': transcript.language,
                'duration': transcript.duration,
                'segments': []
            }
            
            # Add timestamped segments
            for segment in transcript.segments:
                transcript_data['segments'].append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
            
            return transcript_data
            
        except Exception as e:
            raise Exception(f"Transcription failed for segment {segment_index}: {str(e)}")
    
    def transcribe_all_segments(self, segment_files: List[str]) -> List[Dict[str, Any]]:
        """Transcribe all audio segments"""
        transcripts = []
        total_segments = len(segment_files)
        
        for i, segment_file in enumerate(segment_files):
            progress = 20 + (i / total_segments) * 50  # 20-70% progress
            self.update_status('processing', int(progress), f'Transcribing segment {i+1}/{total_segments}')
            
            try:
                transcript = self.transcribe_segment(segment_file, i)
                transcripts.append(transcript)
                
                # Save individual transcript
                transcript_file = os.path.join(self.transcripts_dir, f'segment_{i:03d}.json')
                with open(transcript_file, 'w') as f:
                    json.dump(transcript, f, indent=2)
                    
            except Exception as e:
                print(f"Warning: Failed to transcribe segment {i}: {e}")
                # Continue with other segments
                continue
        
        return transcripts
    
    def merge_transcripts(self, transcripts: List[Dict[str, Any]], segment_duration: int) -> Dict[str, Any]:
        """Merge individual transcripts into a complete transcript with global timestamps"""
        merged_transcript = {
            'total_duration': 0,
            'language': transcripts[0]['language'] if transcripts else 'en',
            'full_text': '',
            'segments': []
        }
        
        current_offset = 0
        
        for transcript in transcripts:
            segment_index = transcript['segment_index']
            base_time = segment_index * segment_duration
            
            # Add to full text
            if merged_transcript['full_text']:
                merged_transcript['full_text'] += ' '
            merged_transcript['full_text'] += transcript['text']
            
            # Add segments with adjusted timestamps
            for segment in transcript['segments']:
                merged_segment = {
                    'start': base_time + segment['start'],
                    'end': base_time + segment['end'],
                    'text': segment['text']
                }
                merged_transcript['segments'].append(merged_segment)
            
            # Update total duration
            merged_transcript['total_duration'] = max(
                merged_transcript['total_duration'],
                base_time + transcript['duration']
            )
        
        return merged_transcript
    
    def process_audio(self, segment_duration: int = 600, generate_images: bool = True, generate_videos: bool = False) -> Dict[str, Any]:
        """Main audio processing pipeline"""
        try:
            self.update_status('processing', 5, 'Starting audio processing...')
            
            # Step 1: Segment audio
            segment_files = self.segment_audio(segment_duration)
            
            # Step 2: Transcribe segments
            transcripts = self.transcribe_all_segments(segment_files)
            
            if not transcripts:
                raise Exception("No segments were successfully transcribed")
            
            # Step 3: Merge transcripts
            self.update_status('processing', 75, 'Merging transcripts...')
            full_transcript = self.merge_transcripts(transcripts, segment_duration)
            
            # Save full transcript
            transcript_file = os.path.join(self.job_dir, 'full_transcript.json')
            with open(transcript_file, 'w') as f:
                json.dump(full_transcript, f, indent=2)
            
            self.update_status('completed', 100, 'Audio processing completed successfully')
            
            return {
                'segments_created': len(segment_files),
                'transcripts_generated': len(transcripts),
                'total_duration': full_transcript['total_duration'],
                'estimated_time': len(segment_files) * 2  # Rough estimate
            }
            
        except Exception as e:
            self.update_status('failed', 0, f'Processing failed: {str(e)}')
            raise e

