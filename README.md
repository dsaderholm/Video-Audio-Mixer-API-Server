# Video Audio Mixer API Server

A standalone Flask API server for mixing audio files with video files using FFmpeg. This API allows you to add background music, voiceovers, or any audio to your videos with customizable volume controls.

## Features

- **Simple API**: Single endpoint to mix audio with video
- **Flexible Volume Control**: Use presets or custom volume levels
- **Multiple Format Support**: Supports various video and audio formats
- **Docker Ready**: Complete containerization with Docker and docker-compose
- **Health Monitoring**: Built-in health check endpoint
- **Large File Support**: Handles files up to 500MB
- **Automatic Cleanup**: Temporary files are managed automatically

## Supported Formats

### Video Formats
- MP4, MOV, AVI, MKV, WebM

### Audio Formats  
- MP3, WAV, AAC, OGG, FLAC, M4A

## Quick Start

### Using Docker Compose (Recommended)

1. Clone or download this repository
2. Navigate to the project directory
3. Start the server:

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8049`

### Manual Installation

1. Install Python 3.11+
2. Install FFmpeg
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the server:

```bash
python app/main.py
```

## API Usage

### Health Check

```bash
curl http://localhost:8049/health
```

### Mix Audio with Video

**Endpoint:** `POST /mix`

**Parameters:**
- `video` (file, required): Video file to mix audio with
- `audio` (file, required): Audio file to add to the video
- `volume` (string/float, optional): Volume control (default: 0.5)
- `loop` (string, optional): Whether to loop audio to match video duration (default: 'true')

**Volume Options:**
- `"mix"` - Equal mix of original video audio and new audio (0.5 each)
- `"background"` - Video audio dominant, new audio as background (0.9 video, 0.3 audio)
- `"main"` - New audio dominant, video audio as background (0.2 video, 0.8 audio)
- Custom float value between 0.0 and 2.0 for the audio volume

**Loop Options:**
- `"true"` (default) - Loop audio to match video duration
- `"false"` - Play audio once, silence when audio ends
- Also accepts: `"1"`, `"0"`, `"yes"`, `"no"`, `"on"`, `"off"`

### cURL Examples

#### Basic mixing with default volume:
```bash
curl -X POST http://localhost:8049/mix \
  -F "video=@/path/to/your/video.mp4" \
  -F "audio=@/path/to/your/audio.mp3" \
  -o mixed_video.mp4
```

#### Using volume presets:
```bash
# Background music (quiet)
curl -X POST http://localhost:8049/mix \
  -F "video=@/path/to/your/video.mp4" \
  -F "audio=@/path/to/your/music.mp3" \
  -F "volume=background" \
  -o video_with_background_music.mp4

# Voiceover (dominant)
curl -X POST http://localhost:8049/mix \
  -F "video=@/path/to/your/video.mp4" \
  -F "audio=@/path/to/your/voiceover.wav" \
  -F "volume=main" \
  -o video_with_voiceover.mp4
```

#### Using custom volume level:
```bash
# Custom volume (0.8 for the audio)
curl -X POST http://localhost:8049/mix \
  -F "video=@/path/to/your/video.mp4" \
  -F "audio=@/path/to/your/audio.mp3" \
  -F "volume=0.8" \
  -o mixed_video.mp4
```

#### Controlling audio looping:
```bash
# Loop audio to match video duration (default behavior)
curl -X POST http://localhost:8049/mix \
  -F "video=@/path/to/your/video.mp4" \
  -F "audio=@/path/to/your/music.mp3" \
  -F "loop=true" \
  -o looped_audio_video.mp4

# Play audio only once (no looping)
curl -X POST http://localhost:8049/mix \
  -F "video=@/path/to/your/video.mp4" \
  -F "audio=@/path/to/your/intro.mp3" \
  -F "loop=false" \
  -o single_play_audio.mp4
```

## Response

- **Success**: Returns the mixed video file as a download
- **Error**: Returns JSON with error details

### Error Response Format:
```json
{
  "error": "Description of the error"
}
```

## Configuration

### Environment Variables

- `PYTHONUNBUFFERED=1` - Enable unbuffered Python output
- `PYTHONDONTWRITEBYTECODE=1` - Prevent Python from writing .pyc files

### File Size Limits

- Maximum file size: 500MB
- Can be adjusted by modifying `MAX_CONTENT_LENGTH` in `app/main.py`

## Development

### Project Structure

```
Video-Audio-Mixer-API-Server/
├── app/
│   ├── main.py           # Flask application
│   └── audio_mixer.py    # Audio mixing logic
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker image configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Running in Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run with debug mode
python app/main.py
```

The server will run on `http://localhost:8049` with debug mode enabled.

### Building Docker Image

```bash
# Build the image
docker build -t video-audio-mixer-api .

# Run the container
docker run -p 8049:8049 video-audio-mixer-api
```

## Technical Details

### Audio Mixing Process

The API uses FFmpeg to mix audio streams:

1. **Validation**: Both input files are validated using ffprobe
2. **Volume Control**: Audio levels are adjusted using FFmpeg filters
3. **Mixing**: Original video audio and new audio are mixed using `amix` filter
4. **Encoding**: Output is encoded with AAC audio and copied video stream
5. **Optimization**: Output is optimized for web playback with `faststart` flag

### FFmpeg Command Structure

```bash
ffmpeg -y -i video.mp4 -i audio.mp3 \
  -filter_complex "[0:a]volume=0.5[a1];[1:a]volume=0.5[a2];[a1][a2]amix=inputs=2:duration=first[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -movflags +faststart output.mp4
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed and in PATH
2. **File format not supported**: Check that your files are in supported formats
3. **File too large**: Increase `MAX_CONTENT_LENGTH` if needed
4. **Permission errors**: Ensure the application has write access to `/tmp`

### Logs

The application logs important information. To view logs:

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f video-audio-mixer-api
```

## Performance Considerations

- **Memory Usage**: Large files will consume more memory during processing
- **Processing Time**: Depends on file size and complexity
- **Disk Space**: Temporary files are created during processing
- **Concurrent Requests**: Multiple requests will process simultaneously

## Security Notes

- The API accepts file uploads - ensure proper network security
- Temporary files are created in `/tmp` - monitor disk usage
- No authentication is implemented - add if needed for production use

## License

This project is provided as-is for educational and development purposes.
