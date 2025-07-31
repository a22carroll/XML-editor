"""
DaVinci Resolve project builder from GPT-4o generated script.
"""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add Resolve API path
sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")

# Try importing Resolve API
try:
    import DaVinciResolveScript as dvr_script
    RESOLVE_AVAILABLE = True
except ImportError:
    RESOLVE_AVAILABLE = False
    logger.warning("DaVinci Resolve API not available - using mock mode")


def build_resolve_project(script_file: str, video_dir: str, output_dir: str):
    """Build DaVinci Resolve project from GPT-4o script."""
    
    script = json.loads(Path(script_file).read_text())
    segments = script["segments"]
    
    logger.info(f"Building project with {len(segments)} segments")
    
    if RESOLVE_AVAILABLE:
        return _build_real_project(segments, video_dir, output_dir)
    else:
        return _build_mock_project(segments, video_dir, output_dir)


def _build_real_project(segments, video_dir, output_dir):
    """Build actual DaVinci Resolve project."""
    
    try:
        # Connect to Resolve
        resolve = dvr_script.scriptapp("Resolve")
        if not resolve:
            raise ConnectionError("Could not connect to Resolve")
        
        # Create project
        pm = resolve.GetProjectManager()
        project = pm.CreateProject("AI Generated Edit")
        if not project:
            raise RuntimeError("Failed to create project")
        
        # Create timeline
        timeline = project.CreateTimeline("AI Edit Timeline")
        if not timeline:
            raise RuntimeError("Failed to create timeline")
        
        media_pool = project.GetMediaPool()
        
        # Import video files
        video_files = list({Path(video_dir) / seg["source_video"] for seg in segments})
        valid_files = [str(f) for f in video_files if f.exists()]
        
        if not valid_files:
            raise RuntimeError(f"No video files found in {video_dir}")
        
        clips = media_pool.ImportMedia(valid_files)
        if not clips:
            raise RuntimeError("Failed to import media")
        
        logger.info(f"Imported {len(clips)} video files")
        
        # Add segments to timeline
        fps = 24
        timeline_pos = 0
        
        for seg in segments:
            # Find matching clip
            clip = None
            for c in clips:
                if hasattr(c, 'GetClipProperty') and seg["source_video"] in str(c.GetClipProperty("File Name")):
                    clip = c
                    break
            
            if clip:
                # Add clip segment to timeline
                timeline.AppendToTrack([{
                    "mediaPoolItem": clip,
                    "startFrame": int(seg["start_time"] * fps),
                    "endFrame": int(seg["end_time"] * fps),
                    "trackIndex": 1,
                    "recordFrame": int(timeline_pos * fps)
                }], 1)
                
                logger.info(f"Added: {seg['text'][:50]}...")
                timeline_pos += seg["duration"]
            else:
                logger.warning(f"Clip not found for: {seg['source_video']}")
        
        # Save project
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        project_path = Path(output_dir) / "project.drp"
        
        # Note: Resolve doesn't have a direct export project method in all versions
        # The project is saved automatically in Resolve's database
        logger.info(f"Project created in Resolve: {project.GetName()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Resolve build failed: {e}")
        return _build_mock_project(segments, video_dir, output_dir)


def _build_mock_project(segments, video_dir, output_dir):
    """Generate mock project with XML export when Resolve unavailable."""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create mock project data
    mock_project = {
        "project_name": "AI Generated Edit",
        "timeline_name": "AI Edit Timeline", 
        "segments": segments,
        "total_duration": sum(seg["duration"] for seg in segments),
        "video_files": list({seg["source_video"] for seg in segments})
    }
    
    # Save mock project
    project_path = Path(output_dir) / "project.json"
    project_path.write_text(json.dumps(mock_project, indent=2))
    
    # Generate Premiere Pro XML
    xml_path = Path(output_dir) / "project.xml"
    _generate_premiere_xml(segments, video_dir, xml_path)
    
    # Generate timeline summary
    summary_path = Path(output_dir) / "edit_summary.txt"
    with summary_path.open('w') as f:
        f.write("AI Generated Edit Summary\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Total Duration: {mock_project['total_duration']:.1f}s\n")
        f.write(f"Total Segments: {len(segments)}\n\n")
        f.write("Timeline:\n")
        f.write("-" * 15 + "\n")
        
        pos = 0
        for i, seg in enumerate(segments, 1):
            f.write(f"{i:2d}. [{pos:5.1f}s] {seg['text'][:60]}...\n")
            f.write(f"    Source: {seg['source_video']} ({seg['start_time']:.1f}-{seg['end_time']:.1f}s)\n")
            pos += seg["duration"]
    
    logger.info(f"Mock project saved: {project_path}")
    logger.info(f"Premiere Pro XML saved: {xml_path}")
    logger.info(f"Summary saved: {summary_path}")
    
    return True


def _generate_premiere_xml(segments, video_dir, xml_path):
    """Generate Premiere Pro compatible XML file."""
    
    # Get unique video files
    video_files = list({seg["source_video"] for seg in segments})
    
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="5">
  <project>
    <name>AI Generated Edit</name>
    <children>
      <bin>
        <name>Media</name>
        <children>'''
    
    # Add media files
    for i, video_file in enumerate(video_files):
        video_path = Path(video_dir) / video_file
        xml_content += f'''
          <clip id="clip{i+1}">
            <name>{video_file}</name>
            <duration>72000</duration>
            <rate>
              <timebase>24</timebase>
              <ntsc>FALSE</ntsc>
            </rate>
            <media>
              <video>
                <track>
                  <clipitem id="clipitem{i+1}">
                    <name>{video_file}</name>
                    <duration>72000</duration>
                    <rate>
                      <timebase>24</timebase>
                      <ntsc>FALSE</ntsc>
                    </rate>
                    <file id="file{i+1}">
                      <name>{video_file}</name>
                      <pathurl>file://localhost/{str(video_path).replace("\\", "/")}</pathurl>
                      <rate>
                        <timebase>24</timebase>
                        <ntsc>FALSE</ntsc>
                      </rate>
                      <duration>72000</duration>
                      <media>
                        <video>
                          <duration>72000</duration>
                          <samplecharacteristics>
                            <rate>
                              <timebase>24</timebase>
                              <ntsc>FALSE</ntsc>
                            </rate>
                            <width>1920</width>
                            <height>1080</height>
                          </samplecharacteristics>
                        </video>
                      </media>
                    </file>
                  </clipitem>
                </track>
              </video>
            </media>
          </clip>'''
    
    xml_content += '''
        </children>
      </bin>
      <sequence>
        <name>AI Edit Timeline</name>
        <duration>72000</duration>
        <rate>
          <timebase>24</timebase>
          <ntsc>FALSE</ntsc>
        </rate>
        <media>
          <video>
            <track>'''
    
    # Add timeline clips
    timeline_pos = 0
    for i, seg in enumerate(segments):
        # Find video file index
        video_idx = video_files.index(seg["source_video"]) + 1
        
        start_frame = int(seg["start_time"] * 24)
        end_frame = int(seg["end_time"] * 24)
        duration_frames = end_frame - start_frame
        timeline_start = int(timeline_pos * 24)
        timeline_end = timeline_start + duration_frames
        
        xml_content += f'''
              <clipitem id="timeline_clip{i+1}">
                <name>{seg["source_video"]}</name>
                <duration>{duration_frames}</duration>
                <rate>
                  <timebase>24</timebase>
                  <ntsc>FALSE</ntsc>
                </rate>
                <start>{timeline_start}</start>
                <end>{timeline_end}</end>
                <in>{start_frame}</in>
                <out>{end_frame}</out>
                <file id="file{video_idx}"/>
              </clipitem>'''
        
        timeline_pos += seg["duration"]
    
    xml_content += '''
            </track>
          </video>
        </media>
      </sequence>
    </children>
  </project>
</xmeml>'''
    
    # Save XML file
    xml_path.write_text(xml_content, encoding='utf-8')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_resolve_project("temp/script.json", "input/videos", "output")