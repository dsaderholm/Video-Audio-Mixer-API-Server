from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
import logging
import traceback
from audio_mixer import AudioMixer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB limit

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_audio_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

def cleanup_temp_files(files):
    """Safely cleanup temporary files"""
    for file_path in files:
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up {file_path}: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Video Audio Mixer API'}), 200

@app.route('/mix', methods=['POST'])
def mix_video_audio():
    """
    Mix audio with video
    
    Parameters:
    - video: Video file (required)
    - audio: Audio file (required) 
    - volume: Audio volume level (optional, default: 0.5)
              Can be a float between 0.0 and 2.0
              Or one of the presets: 'mix', 'background', 'main'
    - loop: Whether to loop audio to match video duration (optional, default: true)
            Accepts: 'true', 'false', '1', '0', 'yes', 'no', 'on', 'off'
    
    Returns:
    - Mixed video file
    """
    temp_files = []  # Keep track of temporary files to clean up

    try:
        # Validate request content type
        if not request.content_type or 'multipart/form-data' not in request.content_type:
            return jsonify({'error': 'Invalid content type. Must be multipart/form-data'}), 400

        # Check if video file is provided
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        video_file = request.files['video']
        audio_file = request.files['audio']
        
        # Validate files
        if not video_file or not video_file.filename:
            return jsonify({'error': 'No video file selected'}), 400
        
        if not audio_file or not audio_file.filename:
            return jsonify({'error': 'No audio file selected'}), 400
        
        if not allowed_video_file(video_file.filename):
            return jsonify({'error': f'Invalid video file type. Allowed types are: {", ".join(ALLOWED_VIDEO_EXTENSIONS)}'}), 400

        if not allowed_audio_file(audio_file.filename):
            return jsonify({'error': f'Invalid audio file type. Allowed types are: {", ".join(ALLOWED_AUDIO_EXTENSIONS)}'}), 400

        # Get volume parameter
        volume = request.form.get('volume', '0.5')
        
        # Get loop parameter
        loop_audio = request.form.get('loop', 'true').lower() in ('true', '1', 'yes', 'on')
        
        # Validate and process volume parameter
        try:
            # Check if it's a preset
            if volume in ['mix', 'background', 'main']:
                volume_level = volume
            else:
                # Try to convert to float
                volume_float = float(volume)
                if volume_float < 0.0 or volume_float > 2.0:
                    return jsonify({'error': 'Volume must be between 0.0 and 2.0'}), 400
                volume_level = volume_float
        except ValueError:
            return jsonify({'error': 'Invalid volume parameter. Must be a number between 0.0-2.0 or one of: mix, background, main'}), 400

        # Save video to temporary file
        temp_suffix = os.urandom(8).hex()
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=f'_video_{temp_suffix}.mp4')
        temp_files.append(temp_video.name)
        
        try:
            video_file.save(temp_video.name)
            logger.info(f"Video saved temporarily as {temp_video.name}")
        except Exception as e:
            logger.error(f"Error saving video file: {str(e)}")
            return jsonify({'error': 'Error saving video file'}), 500

        # Save audio to temporary file
        audio_extension = audio_file.filename.rsplit('.', 1)[1].lower()
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=f'_audio_{temp_suffix}.{audio_extension}')
        temp_files.append(temp_audio.name)
        
        try:
            audio_file.save(temp_audio.name)
            logger.info(f"Audio saved temporarily as {temp_audio.name}")
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            return jsonify({'error': 'Error saving audio file'}), 500

        # Mix audio with video
        try:
            mixer = AudioMixer()
            output_path = mixer.mix_audio(
                temp_video.name,
                temp_audio.name,
                volume_level,
                loop_audio
            )
            temp_files.append(output_path)
            logger.info(f"Audio mixing completed: {output_path}")
        except Exception as e:
            logger.error(f"Error mixing audio: {str(e)}")
            return jsonify({'error': f'Error mixing audio: {str(e)}'}), 500

        # Return the mixed video file
        try:
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f'mixed_video_{temp_suffix}.mp4',
                mimetype='video/mp4'
            )
        except Exception as e:
            logger.error(f"Error sending file: {str(e)}")
            return jsonify({'error': 'Error sending mixed video file'}), 500

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error in mix_video_audio: {str(e)}\n{error_trace}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    
    finally:
        # Note: We don't cleanup immediately since we're sending the file
        # The temp files will be cleaned up by the OS eventually
        pass

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 500MB'}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8049, debug=True)
