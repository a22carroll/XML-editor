"""
Timecode utilities for multicam synchronization.
"""

import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_video_timecode(video_path: Path) -> Optional[str]:
    """
    Extract timecode from video file using ffprobe.
    
    Returns:
        Timecode string in format "HH:MM:SS:FF" or None if not found
    """
    # Try multiple methods to get timecode
    timecode_methods = [
        # Method 1: Stream timecode tag
        [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
            '-show_entries', 'stream_tags=timecode', 
            '-of', 'csv=p=0', str(video_path)
        ],
        # Method 2: Format timecode tag
        [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
            '-show_entries', 'format_tags=timecode', 
            '-of', 'csv=p=0', str(video_path)
        ],
        # Method 3: Creation time (fallback)
        [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
            '-show_entries', 'stream_tags=creation_time', 
            '-of', 'csv=p=0', str(video_path)
        ]
    ]
    
    for i, cmd in enumerate(timecode_methods):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            timecode = result.stdout.strip()
            
            if timecode and timecode != 'N/A':
                logger.info(f"Found timecode for {video_path.name} using method {i+1}: {timecode}")
                
                # Convert creation_time to timecode format if needed
                if i == 2:  # creation_time method
                    timecode = creation_time_to_timecode(timecode)
                
                return timecode
                
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.debug(f"Timecode method {i+1} failed for {video_path.name}: {e}")
            continue
    
    logger.warning(f"No timecode found for {video_path.name}")
    return None


def creation_time_to_timecode(creation_time: str) -> str:
    """
    Convert creation_time to timecode format.
    
    Args:
        creation_time: ISO format like "2024-07-30T10:15:30.000000Z"
    
    Returns:
        Timecode string like "10:15:30:00"
    """
    try:
        # Parse ISO format
        dt = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
        return f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}:00"
    except Exception as e:
        logger.warning(f"Could not parse creation_time {creation_time}: {e}")
        return "00:00:00:00"


def timecode_to_seconds(timecode: str) -> float:
    """
    Convert timecode string to seconds.
    
    Args:
        timecode: Format "HH:MM:SS:FF" where FF is frames (assuming 24fps)
    
    Returns:
        Total seconds as float
    """
    try:
        parts = timecode.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid timecode format: {timecode}")
        
        hours, minutes, seconds, frames = map(int, parts)
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + frames / 24.0
        return total_seconds
        
    except Exception as e:
        logger.error(f"Could not convert timecode {timecode} to seconds: {e}")
        return 0.0


def seconds_to_timecode(seconds: float, fps: float = 24.0) -> str:
    """
    Convert seconds to timecode string.
    
    Args:
        seconds: Time in seconds
        fps: Frame rate (default 24fps)
    
    Returns:
        Timecode string in format "HH:MM:SS:FF"
    """
    try:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        frames = int((seconds % 1) * fps)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
        
    except Exception as e:
        logger.error(f"Could not convert {seconds} seconds to timecode: {e}")
        return "00:00:00:00"


def calculate_sync_offsets(angle_timecodes: Dict[str, str]) -> Dict[str, float]:
    """
    Calculate sync offsets for camera angles based on timecodes.
    
    Args:
        angle_timecodes: Dict mapping angle names to timecode strings
        
    Returns:
        Dict mapping angle names to offset in seconds (relative to earliest)
    """
    if not angle_timecodes:
        return {}
    
    # Convert all timecodes to seconds
    angle_seconds = {}
    for angle, timecode in angle_timecodes.items():
        if timecode:
            angle_seconds[angle] = timecode_to_seconds(timecode)
        else:
            logger.warning(f"No timecode for angle {angle}, using 0.0")
            angle_seconds[angle] = 0.0
    
    # Find the earliest timecode (this becomes our reference point)
    earliest_time = min(angle_seconds.values())
    logger.info(f"Earliest timecode: {seconds_to_timecode(earliest_time)}")
    
    # Calculate offsets relative to earliest
    sync_offsets = {}
    for angle, time_seconds in angle_seconds.items():
        offset = time_seconds - earliest_time
        sync_offsets[angle] = offset
        logger.info(f"Angle {angle}: offset {offset:.3f}s")
    
    return sync_offsets


def get_multicam_sync_data(camera_folders: Dict[str, str]) -> Dict[str, Dict]:
    """
    Get synchronization data for all camera angles.
    
    Args:
        camera_folders: Dict mapping angle names to folder paths
        
    Returns:
        Dict with sync data for each angle
    """
    sync_data = {}
    
    for angle_name, folder_path in camera_folders.items():
        folder = Path(folder_path)
        
        # Get first video file from this angle
        video_files = []
        for ext in ['.mp4', '.mov', '.mxf', '.avi']:  # Common formats
            video_files.extend(folder.glob(f"*{ext}"))
            video_files.extend(folder.glob(f"*{ext.upper()}"))
        
        if not video_files:
            logger.warning(f"No video files found in {folder_path}")
            sync_data[angle_name] = {
                'timecode': None,
                'first_file': None,
                'offset': 0.0
            }
            continue
        
        # Use first video file for sync reference
        first_file = sorted(video_files)[0]
        timecode = get_video_timecode(first_file)
        
        sync_data[angle_name] = {
            'timecode': timecode,
            'first_file': str(first_file),
            'offset': 0.0  # Will be calculated later
        }
        
        logger.info(f"Angle {angle_name}: {first_file.name} -> {timecode}")
    
    # Calculate relative offsets
    angle_timecodes = {name: data['timecode'] for name, data in sync_data.items()}
    offsets = calculate_sync_offsets(angle_timecodes)
    
    # Update sync data with calculated offsets
    for angle_name in sync_data:
        sync_data[angle_name]['offset'] = offsets.get(angle_name, 0.0)
    
    return sync_data


if __name__ == "__main__":
    # Test the functions
    logging.basicConfig(level=logging.INFO)
    
    # Test timecode conversion
    tc = "10:15:30:12"
    seconds = timecode_to_seconds(tc)
    back_to_tc = seconds_to_timecode(seconds)
    print(f"Original: {tc} -> {seconds}s -> {back_to_tc}")