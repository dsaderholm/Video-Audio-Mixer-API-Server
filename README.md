# Video Audio Mixer API Server

A Flask-based API server that mixes audio files with video files using FFmpeg, now optimized to use audio files from a Docker volume.

## Features

- Mix audio files with video files
- Audio files stored in Docker volume (no upload required)
- Volume control with presets (mix, background, main) or custom levels
- Audio looping to match video duration
- Health check and status endpoints
- List available audio files
- Thread-safe processing with concurrent request protection

## New API Usage

### Setup Audio Files

1. The audio files are stored in a Docker volume named `audio_files`
2. Copy your audio files to the volume using docker cp:

```bash
# Copy files to the volume (container must be running)
docker cp your_audio_file.mp3 video-audio-mixer-api:/app/audio/

# Or copy multiple files
docker cp /path/to/your/audio/files/. video-audio-mixer-api:/app/audio/
```

3. The volume persists between container restarts automatically

### API Endpoints

#### List Available Audio Files
```bash
curl http://10.20.0.18:8049/list-audio
```

#### Mix Video with Audio
```bash
curl -X POST http://10.20.0.18:8049/mix \
  -F "video=@/path/to/your/video.mp4" \
  -F "audio_filename=background_music.mp3" \
  -F "volume=background" \
  -F "loop=true"
```

### Parameters

- `video`: Video file (uploaded)
- `audio_filename`: Name of audio file in the volume (string)
- `volume`: Volume control (optional, default: 0.5)
  - Presets: `mix`, `background`, `main`
  - Custom: Float between 0.0-2.0
- `loop`: Loop audio to match video duration (optional, default: true)
  - Values: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`

### Volume Presets

- **`mix`**: Equal mix (video: 50%, audio: 50%)
- **`background`**: Video dominant (video: 90%, audio: 30%)
- **`main`**: Audio dominant (video: 20%, audio: 80%)

## Quick Start

1. **Build and start the container:**
```bash
docker-compose up -d --build
```

2. **Add audio files to the volume:**
```bash
# Copy audio files to the Docker volume
docker cp your_music.mp3 video-audio-mixer-api:/app/audio/
docker cp /path/to/audio/files/. video-audio-mixer-api:/app/audio/
```

3. **List available audio files:**
```bash
curl http://10.20.0.18:8049/list-audio
```

4. **Mix a video with audio:**
```bash
curl -X POST http://10.20.0.18:8049/mix \
  -F "video=@video.mp4" \
  -F "audio_filename=music.mp3" \
  -F "volume=background" \
  -F "loop=true" \
  --output mixed_video.mp4
```

## Examples

### Background Music
```bash
curl -X POST http://10.20.0.18:8049/mix \
  -F "video=@presentation.mp4" \
  -F "audio_filename=soft_piano.mp3" \
  -F "volume=background" \
  -F "loop=true" \
  --output presentation_with_music.mp4
```

### Voice Over
```bash
curl -X POST http://10.20.0.18:8049/mix \
  -F "video=@tutorial.mp4" \
  -F "audio_filename=narration.wav" \
  -F "volume=main" \
  -F "loop=false" \
  --output tutorial_with_voice.mp4
```

### Custom Volume
```bash
curl -X POST http://10.20.0.18:8049/mix \
  -F "video=@demo.mp4" \
  -F "audio_filename=sound_effect.mp3" \
  -F "volume=0.8" \
  -F "loop=true" \
  --output demo_with_effects.mp4
```

## Testing

Use the provided test script:
```bash
python test_api_volume.py
```

## Supported Formats

### Video Formats
- MP4, MOV, AVI, MKV, WebM

### Audio Formats  
- MP3, WAV, AAC, OGG, FLAC, M4A

## Configuration

### File Size Limits
- Maximum file size: 500MB

### Docker Volume
The audio files are stored in a regular Docker volume named `audio_files`. This volume:
- Persists between container restarts
- Is managed by Docker
- Doesn't require host filesystem paths

To manage the volume:
```bash
# View volume info
docker volume inspect video-audio-mixer-api-server_audio_files

# Remove volume (will delete all audio files)
docker volume rm video-audio-mixer-api-server_audio_files
```

## Health Check

Check if the service is running:
```bash
curl http://10.20.0.18:8049/health
```

## Processing Status

Check if processing is in progress:
```bash
curl http://10.20.0.18:8049/status
```

## Migration from File Upload Version

If you're migrating from the previous version that required audio file uploads:

1. **Old API call:**
```bash
curl -X POST http://10.20.0.18:8049/mix \
  -F "video=@video.mp4" \
  -F "audio=@background_music.mp3" \
  -F "volume=background" \
  -F "loop=true"
```

2. **New API call:**
```bash
# First, copy the audio file to the Docker volume
docker cp background_music.mp3 video-audio-mixer-api:/app/audio/

# Then use the filename instead of uploading
curl -X POST http://10.20.0.18:8049/mix \
  -F "video=@video.mp4" \
  -F "audio_filename=background_music.mp3" \
  -F "volume=background" \
  -F "loop=true"
```

## Troubleshooting

### Audio File Not Found
- Ensure the audio file exists in the Docker volume
- Use `docker exec video-audio-mixer-api ls -la /app/audio/` to list files
- Verify the filename matches exactly (case-sensitive)
- Copy files using `docker cp` as shown above

### Volume Issues
- The volume is managed by Docker automatically
- Check if files exist: `docker exec video-audio-mixer-api ls -la /app/audio/`
- View volume details: `docker volume inspect video-audio-mixer-api-server_audio_files`

### FFmpeg Errors
- Check that input files are not corrupted
- Verify supported formats are being used
- Check container logs: `docker logs video-audio-mixer-api`
