import os
import json
import re
from typing import List, Dict, Any, Tuple
import openai
from datetime import datetime

class ContentAnalyzer:
    def __init__(self, job_dir: str):
        self.job_dir = job_dir
        self.client = openai.OpenAI()
        self.analysis_dir = os.path.join(job_dir, 'analysis')
        os.makedirs(self.analysis_dir, exist_ok=True)
    
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
    
    def load_transcript(self) -> Dict[str, Any]:
        """Load the full transcript"""
        transcript_file = os.path.join(self.job_dir, 'full_transcript.json')
        if not os.path.exists(transcript_file):
            raise FileNotFoundError("Transcript not found. Please process audio first.")
        
        with open(transcript_file, 'r') as f:
            return json.load(f)
    
    def extract_topics_and_entities(self, text: str) -> Dict[str, Any]:
        """Use GPT-4 to extract topics, entities, and visual concepts from text"""
        prompt = f"""
        Analyze the following podcast transcript and extract:
        1. Main topics and themes discussed
        2. Named entities (people, places, organizations, events)
        3. Visual concepts that could be illustrated with images
        4. Emotional tone and context for each segment
        5. Specific moments that would benefit from visual illustration

        Please provide the response in JSON format with the following structure:
        {{
            "topics": ["topic1", "topic2", ...],
            "entities": {{
                "people": ["person1", "person2", ...],
                "places": ["place1", "place2", ...],
                "organizations": ["org1", "org2", ...],
                "events": ["event1", "event2", ...]
            }},
            "visual_concepts": [
                {{
                    "concept": "description of visual concept",
                    "search_query": "optimized search query for finding images",
                    "type": "photo|illustration|diagram",
                    "relevance_score": 0.8
                }},
                ...
            ],
            "illustration_moments": [
                {{
                    "description": "what should be illustrated",
                    "search_queries": ["query1", "query2"],
                    "generate_if_not_found": true,
                    "priority": "high|medium|low"
                }},
                ...
            ]
        }}

        Transcript:
        {text[:4000]}  # Limit to avoid token limits
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert content analyzer specializing in podcast content and visual storytelling."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(content)
                
        except Exception as e:
            print(f"Error in content analysis: {e}")
            # Return basic fallback analysis
            return {
                "topics": ["podcast", "conversation"],
                "entities": {"people": [], "places": [], "organizations": [], "events": []},
                "visual_concepts": [],
                "illustration_moments": []
            }
    
    def analyze_segment_for_visuals(self, segment_text: str, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Analyze a specific segment for visual opportunities"""
        prompt = f"""
        Analyze this podcast segment (from {start_time:.1f}s to {end_time:.1f}s) and suggest specific visual content:

        Segment text: "{segment_text}"

        Provide 1-3 specific visual suggestions in JSON format:
        [
            {{
                "timestamp": {start_time},
                "duration": {end_time - start_time},
                "description": "what to show visually",
                "search_queries": ["specific search query"],
                "image_prompt": "detailed prompt for AI image generation if needed",
                "type": "photo|illustration|meme|diagram",
                "priority": 0.8
            }}
        ]

        Focus on:
        - Concrete nouns and concepts that can be visualized
        - People, places, or things mentioned
        - Emotions or reactions that could be illustrated
        - Memes or cultural references
        - Abstract concepts that could be represented visually
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a visual content specialist for podcast illustration."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(content)
                
        except Exception as e:
            print(f"Error analyzing segment: {e}")
            return []
    
    def create_visual_timeline(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a timeline of visual content opportunities"""
        visual_timeline = []
        segments = transcript.get('segments', [])
        
        # Group segments into larger chunks for analysis (every 30-60 seconds)
        chunk_duration = 45  # seconds
        current_chunk = []
        chunk_start = 0
        
        for segment in segments:
            if segment['end'] - chunk_start > chunk_duration or segment == segments[-1]:
                if current_chunk:
                    # Analyze this chunk
                    chunk_text = ' '.join([s['text'] for s in current_chunk])
                    chunk_end = current_chunk[-1]['end']
                    
                    visual_suggestions = self.analyze_segment_for_visuals(
                        chunk_text, chunk_start, chunk_end
                    )
                    
                    visual_timeline.extend(visual_suggestions)
                
                # Start new chunk
                current_chunk = [segment]
                chunk_start = segment['start']
            else:
                current_chunk.append(segment)
        
        # Sort by timestamp
        visual_timeline.sort(key=lambda x: x.get('timestamp', 0))
        return visual_timeline
    
    def analyze_content(self) -> Dict[str, Any]:
        """Main content analysis pipeline"""
        try:
            self.update_status('analyzing', 80, 'Analyzing content for visual opportunities...')
            
            # Load transcript
            transcript = self.load_transcript()
            
            # Extract overall topics and entities
            overall_analysis = self.extract_topics_and_entities(transcript['full_text'])
            
            # Create visual timeline
            self.update_status('analyzing', 85, 'Creating visual timeline...')
            visual_timeline = self.create_visual_timeline(transcript)
            
            # Combine analysis results
            analysis_result = {
                'overall_analysis': overall_analysis,
                'visual_timeline': visual_timeline,
                'total_visual_moments': len(visual_timeline),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Save analysis results
            analysis_file = os.path.join(self.analysis_dir, 'content_analysis.json')
            with open(analysis_file, 'w') as f:
                json.dump(analysis_result, f, indent=2)
            
            self.update_status('analyzed', 90, 'Content analysis completed')
            
            return analysis_result
            
        except Exception as e:
            self.update_status('failed', 0, f'Content analysis failed: {str(e)}')
            raise e
    
    def get_search_queries(self, max_queries: int = 20) -> List[Dict[str, Any]]:
        """Get prioritized search queries for image/video content"""
        analysis_file = os.path.join(self.analysis_dir, 'content_analysis.json')
        if not os.path.exists(analysis_file):
            raise FileNotFoundError("Content analysis not found. Please analyze content first.")
        
        with open(analysis_file, 'r') as f:
            analysis = json.load(f)
        
        queries = []
        
        # Add queries from visual timeline
        for moment in analysis['visual_timeline']:
            for query in moment.get('search_queries', []):
                queries.append({
                    'query': query,
                    'timestamp': moment.get('timestamp', 0),
                    'type': moment.get('type', 'photo'),
                    'priority': moment.get('priority', 0.5),
                    'description': moment.get('description', ''),
                    'image_prompt': moment.get('image_prompt', '')
                })
        
        # Add queries from overall analysis
        for concept in analysis['overall_analysis'].get('visual_concepts', []):
            queries.append({
                'query': concept['search_query'],
                'timestamp': 0,  # General concept, no specific timestamp
                'type': concept['type'],
                'priority': concept['relevance_score'],
                'description': concept['concept'],
                'image_prompt': concept['concept']
            })
        
        # Sort by priority and limit
        queries.sort(key=lambda x: x['priority'], reverse=True)
        return queries[:max_queries]

