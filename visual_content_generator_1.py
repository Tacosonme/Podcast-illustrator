import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai

class VisualContentGenerator:
    def __init__(self, job_dir: str):
        self.job_dir = job_dir
        self.images_dir = os.path.join(job_dir, 'images')
        self.videos_dir = os.path.join(job_dir, 'videos')
        self.content_dir = os.path.join(job_dir, 'content')
        
        # Create directories
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
        
        self.client = openai.OpenAI()
    
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
    
    def search_images(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for images using web search"""
        try:
            # Use omni_search to find relevant images
            import subprocess
            import json
            
            # Create a temporary script to use omni_search
            search_script = f"""
import sys
sys.path.append('/home/ubuntu')
from omni_search import omni_search

results = omni_search(
    brief="Search for images related to: {query}",
    search_type="image",
    queries=["{query}"],
    max_results={max_results}
)

print(json.dumps(results))
"""
            
            # Write and execute the search script
            script_path = os.path.join(self.content_dir, 'search_script.py')
            with open(script_path, 'w') as f:
                f.write(search_script)
            
            result = subprocess.run([
                'python3', script_path
            ], capture_output=True, text=True, cwd='/home/ubuntu')
            
            if result.returncode == 0:
                search_data = json.loads(result.stdout)
                search_results = []
                
                # Process search results
                for item in search_data.get('images', [])[:max_results]:
                    search_results.append({
                        'url': item.get('url', ''),
                        'title': item.get('title', f'Image for {query}'),
                        'description': item.get('description', f'Image related to {query}'),
                        'source': 'web_search',
                        'relevance_score': 0.8
                    })
                
                return search_results
            else:
                print(f"Search failed: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"Error searching images for '{query}': {e}")
            return []
    
    def download_image(self, url: str, filename: str) -> Optional[str]:
        """Download an image from URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            file_path = os.path.join(self.images_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None
    
    def generate_image(self, prompt: str, filename: str, style: str = "photorealistic") -> Optional[str]:
        """Generate an image using media_generate_image tool"""
        try:
            # Enhance prompt based on style
            enhanced_prompt = self.enhance_image_prompt(prompt, style)
            
            # Use media_generate_image tool via subprocess
            import subprocess
            import json
            
            file_path = os.path.join(self.images_dir, filename)
            
            # Create a script to use media_generate_image
            generation_script = f"""
import sys
sys.path.append('/home/ubuntu')
from media_generate_image import media_generate_image

result = media_generate_image(
    brief="Generate image for podcast illustration",
    images=[{{
        "path": "{file_path}",
        "prompt": "{enhanced_prompt}",
        "aspect_ratio": "landscape"
    }}]
)

print("Image generation completed")
"""
            
            script_path = os.path.join(self.content_dir, 'generate_script.py')
            with open(script_path, 'w') as f:
                f.write(generation_script)
            
            result = subprocess.run([
                'python3', script_path
            ], capture_output=True, text=True, cwd='/home/ubuntu')
            
            if result.returncode == 0 and os.path.exists(file_path):
                return file_path
            else:
                print(f"Image generation failed: {result.stderr}")
                return None
            
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def enhance_image_prompt(self, prompt: str, style: str) -> str:
        """Enhance image generation prompt with style and quality modifiers"""
        style_modifiers = {
            "photorealistic": "photorealistic, high quality, detailed, professional photography",
            "illustration": "digital illustration, artwork, colorful, detailed",
            "meme": "internet meme style, humorous, recognizable format",
            "diagram": "clean diagram, infographic style, clear labels, educational"
        }
        
        modifier = style_modifiers.get(style, style_modifiers["photorealistic"])
        return f"{prompt}, {modifier}"
    
    def generate_video_clip(self, prompt: str, filename: str, reference_image: Optional[str] = None) -> Optional[str]:
        """Generate a short video clip"""
        try:
            # This would use the media_generate_video tool
            # For now, create a placeholder
            video_path = os.path.join(self.videos_dir, filename)
            
            # Create a simple placeholder video file (in real implementation, this would generate actual video)
            with open(video_path, 'w') as f:
                f.write(f"Video placeholder for: {prompt}")
            
            return video_path
            
        except Exception as e:
            print(f"Error generating video: {e}")
            return None
    
    def process_visual_content(self, visual_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process all visual content requests"""
        try:
            self.update_status('generating', 90, 'Generating visual content...')
            
            generated_content = {
                'images': [],
                'videos': [],
                'failed_queries': []
            }
            
            total_queries = len(visual_queries)
            
            for i, query_data in enumerate(visual_queries):
                progress = 90 + (i / total_queries) * 8  # 90-98% progress
                self.update_status('generating', int(progress), f'Processing query {i+1}/{total_queries}')
                
                query = query_data['query']
                timestamp = query_data.get('timestamp', 0)
                content_type = query_data.get('type', 'photo')
                description = query_data.get('description', '')
                image_prompt = query_data.get('image_prompt', query)
                
                # Generate filename
                safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_query = safe_query.replace(' ', '_')[:50]
                
                if content_type == 'video':
                    # Generate video
                    filename = f"{int(timestamp)}_{safe_query}.mp4"
                    video_path = self.generate_video_clip(image_prompt, filename)
                    
                    if video_path:
                        generated_content['videos'].append({
                            'filename': filename,
                            'path': video_path,
                            'timestamp': timestamp,
                            'query': query,
                            'description': description
                        })
                    else:
                        generated_content['failed_queries'].append(query_data)
                
                else:
                    # Try to search for images first
                    search_results = self.search_images(query, max_results=3)
                    
                    image_found = False
                    for j, result in enumerate(search_results):
                        filename = f"{int(timestamp)}_{safe_query}_{j}.jpg"
                        downloaded_path = self.download_image(result['url'], filename)
                        
                        if downloaded_path:
                            generated_content['images'].append({
                                'filename': filename,
                                'path': downloaded_path,
                                'timestamp': timestamp,
                                'query': query,
                                'description': description,
                                'source': 'search',
                                'relevance_score': result['relevance_score']
                            })
                            image_found = True
                            break
                    
                    # If no images found, generate one
                    if not image_found:
                        filename = f"{int(timestamp)}_{safe_query}_generated.png"
                        generated_path = self.generate_image(image_prompt, filename, content_type)
                        
                        if generated_path:
                            generated_content['images'].append({
                                'filename': filename,
                                'path': generated_path,
                                'timestamp': timestamp,
                                'query': query,
                                'description': description,
                                'source': 'generated',
                                'relevance_score': 0.7
                            })
                        else:
                            generated_content['failed_queries'].append(query_data)
            
            # Save content manifest
            manifest_file = os.path.join(self.content_dir, 'visual_content_manifest.json')
            with open(manifest_file, 'w') as f:
                json.dump(generated_content, f, indent=2)
            
            self.update_status('content_ready', 98, 'Visual content generation completed')
            
            return generated_content
            
        except Exception as e:
            self.update_status('failed', 0, f'Visual content generation failed: {str(e)}')
            raise e
    
    def get_content_for_timestamp(self, timestamp: float, window: float = 30.0) -> List[Dict[str, Any]]:
        """Get visual content for a specific timestamp window"""
        manifest_file = os.path.join(self.content_dir, 'visual_content_manifest.json')
        if not os.path.exists(manifest_file):
            return []
        
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        relevant_content = []
        
        # Check images
        for image in manifest.get('images', []):
            img_timestamp = image.get('timestamp', 0)
            if abs(img_timestamp - timestamp) <= window:
                relevant_content.append({
                    'type': 'image',
                    'path': image['path'],
                    'timestamp': img_timestamp,
                    'relevance_score': image.get('relevance_score', 0.5)
                })
        
        # Check videos
        for video in manifest.get('videos', []):
            vid_timestamp = video.get('timestamp', 0)
            if abs(vid_timestamp - timestamp) <= window:
                relevant_content.append({
                    'type': 'video',
                    'path': video['path'],
                    'timestamp': vid_timestamp,
                    'relevance_score': 0.8  # Videos generally more relevant
                })
        
        # Sort by relevance and timestamp proximity
        relevant_content.sort(key=lambda x: (x['relevance_score'], -abs(x['timestamp'] - timestamp)), reverse=True)
        
        return relevant_content

