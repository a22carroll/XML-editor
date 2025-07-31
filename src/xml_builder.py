"""
XML project builder from GPT-4o generated script for Premiere Pro.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def build_xml_project(script_file: str, video_dir: str, output_dir: str):
    """Build Premiere Pro XML project from GPT-4o script."""
    
    script = json.loads(Path(script_file).read_text())
    segments = script["segments"]
    
    logger.info(f"Building XML project with {len(segments)} segments")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create project data
    project_data = {
        "project_name": "AI Generated Edit",
        "timeline_name": "AI Edit Timeline", 
        "segments": segments,
        "total_duration": sum(seg["duration"] for seg in segments),
        "video_files": list({seg["source_video"] for seg in segments})
    }
    
    # Save project JSON
    project_path = Path(output_dir) / "project.json"
    project_path.write_text(json.dumps(project_data, indent=2))
    
    # Generate Premiere Pro XML
    xml_path = Path(output_dir) / "project.xml"
    _generate_premiere_xml(segments, video_dir, xml_path)
    
    # Generate timeline summary
    summary_path = Path(output_dir) / "edit_summary.txt"
    with summary_path.open('w') as f:
        f.write("AI Generated Edit Summary\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Total Duration: {project_data['total_duration']:.1f}s\n")
        f.write(f"Total Segments: {len(segments)}\n\n")
        f.write("Timeline:\n")
        f.write("-" * 15 + "\n")
        
        pos = 0
        for i, seg in enumerate(segments, 1):
            f.write(f"{i:2d}. [{pos:5.1f}s] {seg['text'][:60]}...\n")
            f.write(f"    Source: {seg['source_video']} ({seg['start_time']:.1f}-{seg['end_time']:.1f}s)\n")
            pos += seg["duration"]
    
    logger.info(f"Project data saved: {project_path}")
    logger.info(f"Premiere Pro XML saved: {xml_path}")
    logger.info(f"Timeline summary saved: {summary_path}")
    
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
                      <pathurl>file://localhost/{str(video_path.absolute()).replace("\\", "/")}</pathurl>
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
    build_xml_project("temp/script.json", "input/videos", "output")