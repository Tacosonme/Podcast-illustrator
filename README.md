# 🎙️ Podcast Illustrator

An AI-powered application that automatically creates illustrated videos from podcast audio files.

## Features

- 🎵 **Audio Upload**: Supports MP3, WAV, M4A, FLAC, OGG files up to 200MB
- 🤖 **AI Transcription**: Uses OpenAI Whisper for accurate speech-to-text
- 🎨 **Visual Generation**: Creates relevant images using AI and web search
- 🎬 **Video Creation**: Combines audio with synchronized visual content
- 📊 **Real-time Progress**: Live updates throughout the entire process

## Quick Deploy

### Railway (Recommended)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/podcast-illustrator)

### Heroku
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Environment Variables

Set these in your deployment platform:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables
4. Run: `python app.py`

## API Endpoints

- `POST /api/upload` - Upload audio file
- `POST /api/process/{job_id}` - Start processing
- `GET /api/status/{job_id}` - Check processing status
- `GET /api/download/{job_id}` - Download final video

## Tech Stack

- **Backend**: Flask, OpenAI API, FFmpeg
- **Frontend**: React, Vite, Tailwind CSS
- **Processing**: Python, AI image generation
- **Deployment**: Railway, Heroku, Docker

## License

MIT License
