#!/usr/bin/env python3
"""
Test script for Video Audio Mixer API
"""

import requests
import os
import sys

def test_health_check(base_url):
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_audio_mixing(base_url, video_path, audio_path, volume="mix", loop="true"):
    """Test the audio mixing endpoint"""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return False
    
    try:
        with open(video_path, 'rb') as video_file, open(audio_path, 'rb') as audio_file:
            files = {
                'video': video_file,
                'audio': audio_file
            }
            data = {
                'volume': volume,
                'loop': loop
            }
            
            print(f"🔄 Testing audio mixing with volume: {volume}, loop: {loop}")
            response = requests.post(f"{base_url}/mix", files=files, data=data)
            
            if response.status_code == 200:
                # Save the result
                output_path = f"test_output_{volume}.mp4"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Audio mixing successful")
                print(f"   Output saved as: {output_path}")
                print(f"   File size: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Audio mixing failed with status {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    print(f"   Error: {response.json()}")
                else:
                    print(f"   Response: {response.text}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Audio mixing failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    base_url = "http://localhost:8049"
    
    print("🧪 Testing Video Audio Mixer API")
    print(f"   API URL: {base_url}")
    print()
    
    # Test health check
    if not test_health_check(base_url):
        print("\n❌ API is not available. Make sure the server is running.")
        sys.exit(1)
    
    print()
    
    # Test audio mixing if files are provided
    if len(sys.argv) >= 3:
        video_path = sys.argv[1]
        audio_path = sys.argv[2]
        volume = sys.argv[3] if len(sys.argv) > 3 else "mix"
        
        print("🔄 Testing audio mixing...")
        success = test_audio_mixing(base_url, video_path, audio_path, volume)
        
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Audio mixing test failed!")
            sys.exit(1)
    else:
        print("ℹ️  To test audio mixing, provide video and audio file paths:")
        print(f"   python {sys.argv[0]} <video_file> <audio_file> [volume]")
        print()
        print("Example:")
        print(f"   python {sys.argv[0]} video.mp4 audio.mp3 0.7")
        print(f"   python {sys.argv[0]} video.mp4 audio.mp3 background")

if __name__ == "__main__":
    main()
