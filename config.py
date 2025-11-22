"""
Configuration management for AI Audio Content Processor
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    
    # Whisper Configuration
    WHISPER_MODEL: str = os.getenv('WHISPER_MODEL', 'base')
    # Available models: tiny, base, small, medium, large
    
    # Output Configuration
    OUTPUT_DIR: Path = Path(os.getenv('OUTPUT_DIR', 'output'))
    
    # Processing Settings
    SEGMENT_MIN_WORDS: int = int(os.getenv('SEGMENT_MIN_WORDS', '5'))
    SEGMENT_MAX_WORDS: int = int(os.getenv('SEGMENT_MAX_WORDS', '15'))
    
    # Audio Quality
    AUDIO_QUALITY: str = os.getenv('AUDIO_QUALITY', '192')  # kbps
    
    # YouTube URL (optional)
    URL_YOUTUBE: Optional[str] = os.getenv('URL_YOUTUBE')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        errors = []
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY must be set")
        
        if cls.WHISPER_MODEL not in ['tiny', 'base', 'small', 'medium', 'large']:
            errors.append(f"Invalid WHISPER_MODEL: {cls.WHISPER_MODEL}")
        
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive data)"""
        print("\n=== Configuration ===")    
        print(f"Gemini API Key: {'✓ Set' if cls.GEMINI_API_KEY else '✗ Not set'}")
        print(f"Whisper Model: {cls.WHISPER_MODEL}")
        print(f"Output Directory: {cls.OUTPUT_DIR}")
        print(f"Segment Word Range: {cls.SEGMENT_MIN_WORDS}-{cls.SEGMENT_MAX_WORDS}")
        print("===================\n")


if __name__ == "__main__":
    # Test configuration
    Config.print_config()
    if Config.validate():
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration has errors")
