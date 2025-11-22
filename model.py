"""
AI-Powered Audio Content Processor for Shadowing Practice
Automatically downloads, transcribes, segments, and analyzes audio/video content.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import subprocess
import sys
import google.generativeai as genai
from yt_dlp import YoutubeDL
import librosa
import whisper
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_ffmpeg():
    """Check if FFmpeg is available, install imageio-ffmpeg if not"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg not found. Installing imageio-ffmpeg...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'imageio-ffmpeg'])
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            os.environ['FFMPEG_BINARY'] = ffmpeg_exe
            
            # Add FFmpeg directory to PATH
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)
            if ffmpeg_dir not in os.environ['PATH']:
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']
            
            print("✓ FFmpeg installed successfully via imageio-ffmpeg")
            return True
        except Exception as e:
            print(f"Failed to install FFmpeg: {e}")
            return False


class AudioContentProcessor:
    """Main class for processing audio content with AI assistance"""
    
    def __init__(self):
        """Initialize API clients and models"""
        # Ensure FFmpeg is in PATH
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)
            if ffmpeg_dir not in os.environ['PATH']:
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']
        except ImportError:
            pass
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        self.whisper_model = None
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def download_youtube_audio(self, url: str) -> str:
        """
        Download audio from YouTube URL
        
        Args:
            url: YouTube video URL
            
        Returns:
            Path to downloaded audio file
        """
        output_path = self.output_dir / "%(title)s.%(ext)s"
        
        # Download best audio without conversion (avoid FFmpeg issues)
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
            'outtmpl': str(output_path),
            'quiet': False,
            'no_warnings': False,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # If file is webm, try to convert to wav using soundfile/librosa
                if filename.endswith('.webm'):
                    try:
                        print(f"Converting {filename} to WAV format...")
                        import soundfile as sf
                        data, samplerate = sf.read(filename)
                        wav_file = filename.rsplit('.', 1)[0] + '.wav'
                        sf.write(wav_file, data, samplerate)
                        os.remove(filename)  # Remove original webm
                        return wav_file
                    except Exception as e:
                        print(f"Could not convert to WAV: {e}")
                        # Return original file, Whisper can handle webm
                        return filename
                
                return filename
        except Exception as e:
            raise Exception(f"Failed to download audio: {str(e)}")
    
    def transcribe_audio(self, audio_file: str, model: str = "base") -> Dict:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_file: Path to audio file
            model: Whisper model size (tiny, base, small, medium, large)
            
        Returns:
            Transcript with word-level timestamps
        """
        try:
            if self.whisper_model is None:
                print(f"Loading Whisper model: {model}")
                self.whisper_model = whisper.load_model(model)
            
            print(f"Transcribing: {audio_file}")
            result = self.whisper_model.transcribe(
                audio_file,
                word_timestamps=True,
                verbose=True
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def analyze_speech_rate(self, audio_file: str) -> Dict[str, float]:
        """
        Analyze speech rate from audio file
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Dictionary with tempo and speech rate metrics
        """
        try:
            y, sr = librosa.load(audio_file)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            # Calculate speech rate (words per minute estimate)
            duration = librosa.get_duration(y=y, sr=sr)
            
            return {
                'tempo': float(tempo),
                'duration_seconds': float(duration),
                'duration_minutes': float(duration / 60)
            }
        except Exception as e:
            print(f"Warning: Failed to analyze speech rate: {str(e)}")
            return {'tempo': 0, 'duration_seconds': 0, 'duration_minutes': 0}
    
    def ai_segment_transcript(self, transcript: str) -> List[Dict]:
        """
        Use AI to intelligently segment transcript into short phrases
        
        Args:
            transcript: Full transcript text
            
        Returns:
            List of segmented phrases with metadata
        """
        prompt = f"""Chia transcript này thành các segments ngắn (5-15 từ mỗi segment) phù hợp cho luyện shadowing.
        
Yêu cầu:
- Mỗi segment phải là một cụm từ hoàn chỉnh, tự nhiên
- Độ dài 5-15 từ
- Giữ nguyên nội dung gốc
- Trả về JSON array với format: [{{"segment": "text", "word_count": number}}]

Transcript:
{transcript}

Trả về chỉ JSON, không có text khác."""

        try:
            response = self.gemini_model.generate_content(prompt)
            content = response.text
            
            # Extract JSON from response (remove markdown code blocks if present)
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Parse JSON response
            segments = json.loads(content)
            if isinstance(segments, dict) and 'segments' in segments:
                segments = segments['segments']
            return segments
            
        except Exception as e:
            print(f"Warning: AI segmentation failed: {str(e)}")
            # Fallback: simple sentence splitting
            sentences = transcript.split('. ')
            return [{"segment": s.strip(), "word_count": len(s.split())} for s in sentences if s.strip()]
    
    def ai_analyze_metadata(self, transcript: str, audio_metrics: Dict) -> Dict:
        """
        Use AI to analyze and classify audio content
        
        Args:
            transcript: Full transcript text
            audio_metrics: Speech rate and duration metrics
            
        Returns:
            Metadata including difficulty, accent, tags
        """
        prompt = f"""Phân tích audio transcript này và trả về metadata dưới dạng JSON:

Thông tin audio:
- Duration: {audio_metrics.get('duration_minutes', 0):.2f} minutes
- Tempo: {audio_metrics.get('tempo', 0):.0f} BPM

Transcript:
{transcript[:1000]}...

Trả về JSON với format:
{{
    "difficulty": "Beginner|Intermediate|Advanced",
    "accentType": "American|British|Australian|Other",
    "speechRate": "Slow|Normal|Fast",
    "suggestedTags": ["tag1", "tag2", ...],
    "topic": "brief topic description",
    "vocabulary_level": "A1|A2|B1|B2|C1|C2"
}}

Chỉ trả về JSON, không có text khác."""

        try:
            response = self.gemini_model.generate_content(prompt)
            content = response.text
            
            # Extract JSON from response (remove markdown code blocks if present)
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            metadata = json.loads(content)
            return metadata
            
        except Exception as e:
            print(f"Warning: AI metadata analysis failed: {str(e)}")
            # Return default metadata
            return {
                "difficulty": "Intermediate",
                "accentType": "Unknown",
                "speechRate": "Normal",
                "suggestedTags": ["audio"],
                "topic": "General",
                "vocabulary_level": "B1"
            }
    
    def save_shadowing_content(self, data: Dict, output_file: Optional[str] = None) -> str:
        """
        Save processed content to JSON file
        
        Args:
            data: Complete content data
            output_file: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if output_file is None:
            title = data.get('title', 'content').replace(' ', '_')
            output_file = self.output_dir / f"{title}_shadowing.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved content to: {output_file}")
        return str(output_file)
    
    async def create_from_youtube(self, url: str, whisper_model: str = "base") -> Dict:
        """
        Complete pipeline: Download, transcribe, segment, analyze YouTube content
        
        Args:
            url: YouTube video URL
            whisper_model: Whisper model size to use
            
        Returns:
            Complete processed content data
        """
        print(f"\n=== Processing YouTube URL: {url} ===\n")
        
        # Step 1: Download audio
        print("Step 1: Downloading audio...")
        audio_file = self.download_youtube_audio(url)
        print(f"✓ Downloaded: {audio_file}\n")
        
        # Step 2: Transcribe with Whisper
        print("Step 2: Transcribing audio...")
        transcript_data = self.transcribe_audio(audio_file, model=whisper_model)
        full_transcript = transcript_data['text']
        print(f"✓ Transcribed: {len(full_transcript)} characters\n")
        
        # Step 3: Analyze audio metrics
        print("Step 3: Analyzing audio metrics...")
        audio_metrics = self.analyze_speech_rate(audio_file)
        print(f"✓ Duration: {audio_metrics['duration_minutes']:.2f} minutes\n")
        
        # Step 4: Segment transcript with AI
        print("Step 4: Segmenting transcript with AI...")
        segments = self.ai_segment_transcript(full_transcript)
        print(f"✓ Created {len(segments)} segments\n")
        
        # Step 5: Analyze metadata with AI
        print("Step 5: Analyzing metadata with AI...")
        metadata = self.ai_analyze_metadata(full_transcript, audio_metrics)
        print(f"✓ Difficulty: {metadata['difficulty']}, Level: {metadata['vocabulary_level']}\n")
        
        # Step 6: Compile all data
        print("Step 6: Compiling final data...")
        result = {
            'source_url': url,
            'audio_file': audio_file,
            'title': Path(audio_file).stem,
            'transcript': full_transcript,
            'transcript_with_timestamps': transcript_data,
            'segments': segments,
            'audio_metrics': audio_metrics,
            'metadata': metadata,
            'created_at': str(asyncio.get_event_loop().time())
        }
        
        # Step 7: Save to file
        output_path = self.save_shadowing_content(result)
        print(f"✓ Saved to: {output_path}\n")
        
        print("=== Processing Complete! ===\n")
        return result


# Main execution
async def main():
    """Example usage"""
    # Check FFmpeg availability
    if not check_ffmpeg():
        print("\n✗ FFmpeg is required but could not be installed.")
        print("Please install FFmpeg manually:")
        print("  - Windows: winget install -e --id Gyan.FFmpeg")
        print("  - Or download from: https://ffmpeg.org/download.html")
        return
    
    processor = AudioContentProcessor()
    
    # Get YouTube URL from environment or user input
    youtube_url = os.getenv('URL_YOUTUBE', '').strip()
    
    if not youtube_url:
        youtube_url = input("Enter YouTube URL: ").strip()
    else:
        print(f"Using URL from .env: {youtube_url}")
    
    if not youtube_url:
        print("No URL provided. Exiting.")
        return
    
    try:
        # Use Whisper model from environment or default to 'base'
        whisper_model = os.getenv('WHISPER_MODEL', 'base')
        result = await processor.create_from_youtube(youtube_url, whisper_model=whisper_model)
        print("\n✓ Success! Content processed and saved.")
        print(f"Segments: {len(result['segments'])}")
        print(f"Difficulty: {result['metadata']['difficulty']}")
        print(f"Tags: {', '.join(result['metadata']['suggestedTags'])}")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())