"""
Enhanced transcription module with chunking and progressive processing.
"""

import os
import json
import logging
import tempfile
import subprocess
import gc
from pathlib import Path
from typing import List, Dict, Iterator
import math

import whisper

logger = logging.getLogger(__name__)

VIDEO_FORMATS = {
    '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v',
    '.3gp', '.ogv', '.ts', '.mts', '.m2ts', '.vob', '.asf', '.rm',
    '.rmvb', '.divx', '.xvid', '.f4v', '.mpg', '.mpeg', '.m2v', '.mxf'
}

def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        logger.warning(f"Could not get duration for {video_path.name}")
        return 0.0

def extract_audio_chunk(video_path: Path, temp_dir: Path, start_time: float, 
                       chunk_duration: float, chunk_idx: int) -> Path:
    """Extract a specific audio chunk from video."""
    audio_file = temp_dir / f"{video_path.stem}_chunk_{chunk_idx:03d}.wav"
    
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),           # Start time
        '-i', str(video_path),
        '-t', str(chunk_duration),        # Duration
        '-vn',                            # No video
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-af', 'volume=0.8',
        str(audio_file)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return audio_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract chunk {chunk_idx}: {e}")
        raise

def analyze_audio_content(audio_path: Path) -> dict:
    """Analyze extracted audio to check if it contains actual audio data."""
    # Simplified fallback if complex analysis fails
    try:
        cmd = [
            'ffprobe', '-f', 'lavfi', '-i', f'amovie={audio_path},astats=metadata=1:reset=1',
            '-show_entries', 'frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.RMS_level,lavfi.astats.Overall.Peak_level',
            '-of', 'csv=p=0', '-t', '10'  # Analyze first 10 seconds
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        lines = result.stdout.strip().split('\n')
        
        # Check if we have audio levels
        rms_levels = []
        peak_levels = []
        
        for line in lines:
            if line and ',' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        rms_level = float(parts[1]) if parts[1] != 'N/A' else -96.0
                        peak_level = float(parts[2]) if parts[2] != 'N/A' else -96.0
                        rms_levels.append(rms_level)
                        peak_levels.append(peak_level)
                    except ValueError:
                        continue
        
        if rms_levels:
            avg_rms = sum(rms_levels) / len(rms_levels)
            max_peak = max(peak_levels) if peak_levels else -96.0
            
            return {
                "has_audio": True,
                "avg_rms_db": avg_rms,
                "max_peak_db": max_peak,
                "is_silent": avg_rms < -60.0,  # Very quiet
                "sample_count": len(rms_levels)
            }
        else:
            return {"has_audio": False, "is_silent": True}
            
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Audio analysis failed: {e}")
        # Fallback: just check if file has reasonable size
        file_size = audio_path.stat().st_size
        return {
            "has_audio": file_size > 1000,  # Assume audio if file > 1KB
            "analysis_failed": True,
            "fallback_used": True
        }

def extract_audio_for_transcription(video_path: Path, temp_dir: Path) -> Path:
    """Extract complete audio from video for transcription."""
    audio_file = temp_dir / f"{video_path.stem}.wav"
    
    # First, check if the video has audio tracks
    probe_cmd = [
        'ffprobe', '-v', 'quiet', '-select_streams', 'a:0', 
        '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', str(video_path)
    ]
    
    try:
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        if not probe_result.stdout.strip():
            raise RuntimeError("No audio track found in video file")
        logger.info(f"Audio codec detected: {probe_result.stdout.strip()}")
    except subprocess.CalledProcessError:
        logger.warning("Could not probe audio stream - attempting extraction anyway")
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-vn',                        # No video
        '-acodec', 'pcm_s16le',      # 16-bit PCM
        '-ar', '16000',              # 16kHz sample rate
        '-ac', '1',                  # Mono
        '-af', 'volume=3.0,highpass=f=80,lowpass=f=8000',  # Boost volume more and filter noise
        '-loglevel', 'warning',      # Show warnings/errors
        str(audio_file)
    ]
    
    try:
        logger.info(f"Extracting audio from {video_path.name}...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if not audio_file.exists() or audio_file.stat().st_size == 0:
            raise RuntimeError("Audio extraction produced empty file")
        
        audio_size_mb = audio_file.stat().st_size / (1024**2)
        audio_duration = get_audio_duration(audio_file)
        logger.info(f"Audio extracted: {audio_size_mb:.1f} MB, duration: {audio_duration:.1f}s")
        
        if audio_duration == 0:
            raise RuntimeError("Extracted audio has zero duration")
        
        # Analyze the audio content
        audio_analysis = analyze_audio_content(audio_file)
        logger.info(f"Audio analysis: {audio_analysis}")
        
        if audio_analysis.get("is_silent", True):
            logger.warning("Audio appears to be silent or very quiet - transcription may fail")
        
        return audio_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg audio extraction failed: {e}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        raise RuntimeError(f"Could not extract audio from {video_path.name}")

def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', str(audio_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0.0

def cleanup_old_temp_dirs():
    """Clean up any leftover temporary directories from previous runs."""
    import tempfile
    import shutil
    
    temp_root = Path(tempfile.gettempdir())
    
    # Find and remove old audio transcription temp dirs
    for temp_dir in temp_root.glob("audio_transcription_*"):
        if temp_dir.is_dir():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up old temp directory: {temp_dir.name}")
            except Exception as e:
                logger.warning(f"Could not clean up {temp_dir.name}: {e}")

def clear_transcripts_folder(output_dir: str):
    """Optionally clear the transcripts folder before starting."""
    output_path = Path(output_dir)
    if output_path.exists():
        for file in output_path.glob("*.json"):
            try:
                file.unlink()
                logger.info(f"Removed old transcript: {file.name}")
            except Exception as e:
                logger.warning(f"Could not remove {file.name}: {e}")

def transcribe_in_chunks(model, video_path: Path, temp_dir: Path, 
                        chunk_size_minutes: int = 10, force_language: str = "en") -> Dict:
    """
    Transcribe very large files in chunks to manage memory usage.
    """
    duration = get_video_duration(video_path)
    if duration == 0:
        raise RuntimeError("Could not determine video duration")
    
    chunk_duration = chunk_size_minutes * 60  # Convert to seconds
    num_chunks = math.ceil(duration / chunk_duration)
    
    logger.info(f"Transcribing {duration:.1f}s video in {num_chunks} chunks of {chunk_size_minutes} minutes")
    
    all_segments = []
    
    for i in range(num_chunks):
        start_time = i * chunk_duration
        actual_chunk_duration = min(chunk_duration, duration - start_time)
        
        logger.info(f"Processing chunk {i+1}/{num_chunks} ({start_time:.1f}s - {start_time + actual_chunk_duration:.1f}s)")
        
        try:
            # Extract chunk
            chunk_file = extract_audio_chunk(video_path, temp_dir, start_time, 
                                           actual_chunk_duration, i)
            
            # Transcribe chunk with memory-optimized settings and forced language
            result = model.transcribe(
                str(chunk_file),
                word_timestamps=True,
                verbose=False,
                fp16=False,
                temperature=0,
                beam_size=1,
                best_of=1,
                condition_on_previous_text=False,
                language=force_language
            )
            
            # Adjust timestamps to global timeline
            for segment in result["segments"]:
                segment["start"] += start_time
                segment["end"] += start_time
                all_segments.append(segment)
            
            # Clean up chunk file immediately
            chunk_file.unlink()
            
            # Force garbage collection after each chunk
            del result
            gc.collect()
            
        except Exception as e:
            logger.error(f"Failed to process chunk {i+1}: {e}")
            continue
    
    return {
        "segments": all_segments,
        "language": all_segments[0].get("language", "unknown") if all_segments else "unknown"
    }

def get_optimal_whisper_params(file_size_gb: float) -> dict:
    """Get optimal Whisper parameters based on file size."""
    if file_size_gb > 10.0:
        # Extremely large files - use chunking
        return {
            "use_chunking": True,
            "chunk_size_minutes": 5,
            "beam_size": 1,
            "best_of": 1,
            "temperature": 0,
            "condition_on_previous_text": False,
            "verbose": False,
            "fp16": False
        }
    elif file_size_gb > 5.0:
        # Very large files - maximum memory conservation
        return {
            "use_chunking": False,
            "beam_size": 1,
            "best_of": 1, 
            "temperature": 0,
            "condition_on_previous_text": False,
            "verbose": False,
            "fp16": False
        }
    elif file_size_gb > 2.0:
        # Large files - balanced approach
        return {
            "use_chunking": False,
            "beam_size": 2,
            "best_of": 2,
            "temperature": 0,
            "verbose": False,
            "fp16": False
        }
    else:
        # Normal files - default quality
        return {
            "use_chunking": False,
            "verbose": True
        }

def transcribe_videos_enhanced(
    input_dir: str,
    output_dir: str,
    model_size: str = "base",
    large_file_threshold_gb: float = 1.0,
    very_large_file_threshold_gb: float = 10.0,
    force_language: str = "en",
    clear_previous_transcripts: bool = False
) -> List[Path]:
    """
    Enhanced transcription with chunking support for very large files.
    """
    logger.info(f"Loading Whisper model: {model_size}")
    model = whisper.load_model(model_size)

    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    video_files = [f for f in input_path.iterdir() if f.suffix.lower() in VIDEO_FORMATS]
    
    if not video_files:
        logger.warning(f"No video files found in: {input_dir}")
        return []

    logger.info(f"Found {len(video_files)} video files")
    transcript_paths = []

    # Clean up any existing temp directories first
    cleanup_old_temp_dirs()
    
    # Optionally clear previous transcripts (only if parameter is True)
    if clear_previous_transcripts:
        clear_transcripts_folder(output_dir)

    # Create temp directory for audio extraction
    temp_dir = Path(tempfile.mkdtemp(prefix="audio_transcription_"))
    
    try:
        for video_path in video_files:
            try:
                file_size_gb = video_path.stat().st_size / (1024**3)
                logger.info(f"Processing: {video_path.name} ({file_size_gb:.2f} GB)")
                
                # Get optimal parameters for this file size
                params = get_optimal_whisper_params(file_size_gb)
                
                if file_size_gb > very_large_file_threshold_gb and params.get("use_chunking"):
                    # Use chunking for extremely large files
                    logger.info("Very large file detected - using chunked transcription")
                    result = transcribe_in_chunks(
                        model, video_path, temp_dir, 
                        params.get("chunk_size_minutes", 10)
                    )
                    
                elif file_size_gb > large_file_threshold_gb:
                    # Use audio-only transcription for large files
                    logger.info("Large file detected - using audio-only transcription")
                    
                    audio_file = extract_audio_for_transcription(video_path, temp_dir)
                    
                    # Apply memory-optimized parameters with forced language
                    transcribe_params = {k: v for k, v in params.items() 
                                       if k not in ["use_chunking", "chunk_size_minutes"]}
                    transcribe_params["language"] = force_language
                    
                    result = model.transcribe(str(audio_file), word_timestamps=True, **transcribe_params)
                    
                    audio_file.unlink()
                    logger.info("Temporary audio file cleaned up")
                    
                else:
                    # Direct transcription for smaller files
                    logger.info("Direct video transcription")
                    transcribe_params = {k: v for k, v in params.items() 
                                       if k not in ["use_chunking", "chunk_size_minutes"]}
                    transcribe_params["language"] = force_language
                    result = model.transcribe(str(video_path.resolve()), 
                                            word_timestamps=True, **transcribe_params)

                # Process transcript segments
                sentences = [
                    {
                        "text": segment["text"].strip(),
                        "start": segment["start"],
                        "end": segment["end"],
                        "duration": segment["end"] - segment["start"]
                    }
                    for segment in result["segments"]
                    if segment["text"].strip()
                ]

                # Determine transcription method
                if file_size_gb > very_large_file_threshold_gb:
                    method = "chunked_audio"
                elif file_size_gb > large_file_threshold_gb:
                    method = "audio_only"
                else:
                    method = "direct"

                # Create transcript data
                transcript_data = {
                    "video_file": video_path.name,
                    "original_video_path": str(video_path),
                    "language": result.get("language", "unknown"),
                    "sentences": sentences,
                    "file_size_gb": round(file_size_gb, 2),
                    "transcription_method": method,
                    "total_duration": sum(s["duration"] for s in sentences),
                    "processing_parameters": params
                }

                # Save transcript
                output_file = output_path / f"{video_path.stem}.json"
                with output_file.open("w", encoding="utf-8") as f:
                    json.dump(transcript_data, f, indent=2, ensure_ascii=False)

                logger.info(f"Saved transcript: {output_file.name}")
                logger.info(f"Found {len(sentences)} speech segments, total duration: {transcript_data['total_duration']:.1f}s")
                transcript_paths.append(output_file)

                # Force garbage collection after each file
                del result
                gc.collect()

            except Exception as e:
                logger.error(f"Failed to transcribe {video_path.name}: {e}")
                import traceback
                logger.error(f"Full error: {traceback.format_exc()}")
                continue
    
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
            logger.info("Cleaned up temporary directory")

    return transcript_paths

# Alias for backward compatibility
def transcribe_videos(input_dir: str, output_dir: str, model_size: str = "base") -> List[Path]:
    """Backward compatibility wrapper for transcribe_videos_enhanced."""
    return transcribe_videos_enhanced(
        input_dir=input_dir,
        output_dir=output_dir,
        model_size=model_size,
        large_file_threshold_gb=1.0,
        very_large_file_threshold_gb=10.0,
        force_language="en",
        clear_previous_transcripts=False
    )


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 3:
        print("Usage: python transcription.py <input_dir> <output_dir> [model_size]")
        print("Example: python transcription.py 'C:/path/to/videos' 'temp/transcripts' 'base'")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 else "base"
    
    transcribe_videos_enhanced(input_dir, output_dir, model_size)