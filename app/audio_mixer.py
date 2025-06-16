import subprocess
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class AudioMixer:
    def __init__(self):
        self.volume_presets = {
            'mix': ('0.5', '0.5'),      # Equal mix of original video audio and new audio
            'background': ('0.9', '0.3'), # Video audio dominant, new audio as background
            'main': ('0.2', '0.8')       # New audio dominant, video audio as background
        }

    def mix_audio(self, video_path, audio_path, volume='mix', loop_audio=True):
        """
        Mix audio file with video file
        
        Args:
            video_path (str): Path to input video file
            audio_path (str): Path to input audio file
            volume (str or float): Volume control
                - If string: Must be one of 'mix', 'background', 'main'
                - If float: Volume level for the audio (0.0 to 2.0)
            loop_audio (bool): Whether to loop the audio to match video duration
        
        Returns:
            str: Path to output video file with mixed audio
        """
        
        # Create temporary file with a unique name
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f'mixed_output_{os.urandom(8).hex()}.mp4')

        # Validate input files first
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Validate input video file
        try:
            probe_cmd = [
                'ffmpeg', '-v', 'error',
                '-i', video_path,
                '-f', 'null', '-'
            ]
            subprocess.run(probe_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Invalid input video file: {e.stderr}")
            raise ValueError("The input video file appears to be corrupted or invalid")

        # Validate input audio file
        try:
            probe_cmd = [
                'ffmpeg', '-v', 'error',
                '-i', audio_path,
                '-f', 'null', '-'
            ]
            subprocess.run(probe_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Invalid input audio file: {e.stderr}")
            raise ValueError("The input audio file appears to be corrupted or invalid")

        # Determine volume levels
        if isinstance(volume, str) and volume in self.volume_presets:
            video_vol, audio_vol = self.volume_presets[volume]
        elif isinstance(volume, (int, float)):
            # Custom volume level - keep original video audio at 0.5, set new audio to specified level
            video_vol = '0.5'
            audio_vol = str(float(volume))
        else:
            raise ValueError(f"Invalid volume parameter: {volume}. Must be float 0.0-2.0 or one of: {list(self.volume_presets.keys())}")

        # Build FFmpeg command for mixing audio
        if loop_audio:
            # Loop the audio to match video duration
            filter_complex = (
                f'[0:a]volume={video_vol}[a1];'
                f'[1:a]aloop=loop=-1:size=2e+09,volume={audio_vol}[a2];'
                f'[a1][a2]amix=inputs=2:duration=first[aout]'
            )
        else:
            # Don't loop audio, just mix as-is
            filter_complex = (
                f'[0:a]volume={video_vol}[a1];'
                f'[1:a]volume={audio_vol}[a2];'
                f'[a1][a2]amix=inputs=2:duration=first[aout]'
            )
        
        cmd = [
            'ffmpeg',
            '-y',  # Force overwrite
            '-i', video_path,   # Input video
            '-i', audio_path,   # Input audio
            '-filter_complex', filter_complex,
            '-map', '0:v',      # Map video from first input
            '-map', '[aout]',   # Map mixed audio
            '-c:v', 'copy',     # Copy video codec (no re-encoding)
            '-c:a', 'aac',      # Encode audio as AAC
            '-b:a', '192k',     # Audio bitrate
            '-movflags', '+faststart',  # Optimize for web playback
            output_path
        ]

        try:
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully created mixed video: {output_path}")
                return output_path
            else:
                raise subprocess.CalledProcessError(1, cmd, process.stdout, process.stderr)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Error: {e.stderr}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise RuntimeError(f"Failed to mix audio with video: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error during audio mixing: {str(e)}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise

    def get_media_info(self, file_path):
        """
        Get basic media information using ffprobe
        
        Args:
            file_path (str): Path to media file
            
        Returns:
            dict: Media information
        """
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            import json
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting media info: {e.stderr}")
            raise RuntimeError(f"Failed to get media information: {e.stderr}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing ffprobe output: {str(e)}")
            raise RuntimeError("Failed to parse media information")
