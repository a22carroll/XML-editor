"""
Simplified transcription module using Whisper.
"""

import json
import logging
import subprocess
import tempfile
import gc
from pathlib import Path
from typing import List
import whisper

logger = logging.getLogger(__name__)

VIDEO_FORMATS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}


def extract_audio(video_path: Path, temp_dir: Path) -> Path:
    """Extract audio from video for transcription."""
    audio_file = temp_dir / f"{video_path.stem}.wav"
    
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path), '-vn', '-acodec', 'pcm_s16le',
        '-ar', '16000', '-ac', '1', str(audio_file)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        if not audio_file.exists() or audio_file.stat().st_size == 0:
            raise RuntimeError("Audio extraction failed")
        return audio_file
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e}")
        raise


def transcribe_videos(input_dir: str, output_dir: str, model_size: str = "base", audio_only: bool = True) -> List[Path]:
    """Transcribe videos using Whisper with optional audio-only mode for speed."""
    
    logger.info(f"Loading Whisper model: {model_size}")
    model = whisper.load_model(model_size)
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find video files
    video_files = [f for f in input_path.iterdir() if f.suffix.lower() in VIDEO_FORMATS]
    if not video_files:
        logger.warning(f"No video files found in: {input_dir}")
        return []
    
    logger.info(f"Found {len(video_files)} video files")
    transcript_paths = []
    
    # Create temp directory for audio extraction
    temp_dir = Path(tempfile.mkdtemp(prefix="transcription_"))
    
    try:
        for video_path in video_files:
            try:
                file_size_gb = video_path.stat().st_size / (1024**3)
                logger.info(f"Processing: {video_path.name} ({file_size_gb:.2f} GB)")
                
                if audio_only:
                    # Always extract audio first for faster processing
                    logger.info("Extracting audio for faster transcription")
                    audio_file = extract_audio(video_path, temp_dir)
                    result = model.transcribe(
                        str(audio_file),
                        word_timestamps=True,
                        verbose=False,
                        fp16=False,
                        temperature=0
                    )
                    audio_file.unlink()  # Clean up immediately
                else:
                    # Fallback to direct video transcription
                    logger.info("Direct video transcription")
                    result = model.transcribe(str(video_path), word_timestamps=True)
                
                # Process segments into sentences
                sentences = [
                    {
                        "text": seg["text"].strip(),
                        "start": seg["start"],
                        "end": seg["end"],
                        "duration": seg["end"] - seg["start"]
                    }
                    for seg in result["segments"]
                    if seg["text"].strip()
                ]
                
                # Create transcript data - store original video path for XML export
                transcript_data = {
                    "video_file": video_path.name,
                    "original_video_path": str(video_path.absolute()),  # Full path for XML
                    "language": result.get("language", "unknown"),
                    "sentences": sentences,
                    "total_duration": sum(s["duration"] for s in sentences),
                    "transcription_method": "audio_only" if audio_only else "direct"
                }
                
                # Save transcript
                output_file = output_path / f"{video_path.stem}.json"
                output_file.write_text(json.dumps(transcript_data, indent=2, ensure_ascii=False))
                
                logger.info(f"Saved {len(sentences)} segments ({transcript_data['total_duration']:.1f}s) to {output_file.name}")
                transcript_paths.append(output_file)
                
                # Clean up memory
                del result
                gc.collect()
                
            except Exception as e:
                logger.error(f"Failed to transcribe {video_path.name}: {e}")
                continue
    
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
    
    return transcript_paths


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 3:
        print("Usage: python transcription.py <input_dir> <output_dir> [model_size]")
        sys.exit(1)
    
    transcribe_videos(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "base")