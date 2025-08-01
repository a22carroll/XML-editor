"""
XML project builder from GPT-4o generated script for Premiere Pro.
Enhanced with multicam support.
"""

import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


def build_xml_project(script_file: str, video_dir: str, output_dir: str):
    """Build Premiere Pro XML project from GPT-4o script (single camera)."""
    
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


def build_multicam_xml_project(script_file: str, camera_folders: Dict[str, str], sync_data: Dict, output_dir: str):
    """Build Premiere Pro multicam XML project from GPT-4o script."""
    
    script = json.loads(Path(script_file).read_text())
    segments = script["segments"]
    
    logger.info(f"Building multicam XML project with {len(segments)} segments from {len(camera_folders)} angles")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create multicam project data
    project_data = {
        "project_name": "AI Generated Multicam Edit",
        "timeline_name": "Multicam Timeline",
        "type": "multicam",
        "camera_angles": list(camera_folders.keys()),
        "sync_data": sync_data,
        "segments": segments,
        "total_duration": sum(seg["duration"] for seg in segments),
        "angle_usage": _count_angle_usage(segments)
    }
    
    # Save project JSON
    project_path = Path(output_dir) / "project.json"
    project_path.write_text(json.dumps(project_data, indent=2))
    
    # Generate Premiere Pro multicam XML
    xml_path = Path(output_dir) / "project.xml"
    _generate_multicam_premiere_xml(segments, camera_folders, sync_data, xml_path)
    
    # Generate multicam timeline summary
    summary_path = Path(output_dir) / "edit_summary.txt"
    _generate_multicam_summary(project_data, summary_path)
    
    logger.info(f"Multicam project data saved: {project_path}")
    logger.info(f"Multicam Premiere Pro XML saved: {xml_path}")
    logger.info(f"Multicam timeline summary saved: {summary_path}")
    
    return True


def _count_angle_usage(segments):
    """Count how many times each camera angle is used."""
    usage = {}
    for seg in segments:
        angle = seg.get("camera_angle", "unknown")
        usage[angle] = usage.get(angle, 0) + 1
    return usage


def _generate_multicam_summary(project_data, summary_path):
    """Generate detailed multicam editing summary."""
    segments = project_data["segments"]
    
    with summary_path.open('w') as f:
        f.write("AI Generated Multicam Edit Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total Duration: {project_data['total_duration']:.1f}s\n")
        f.write(f"Total Segments: {len(segments)}\n")
        f.write(f"Camera Angles: {len(project_data['camera_angles'])}\n\n")
        
        # Angle usage statistics
        f.write("Camera Angle Usage:\n")
        f.write("-" * 20 + "\n")
        for angle, count in project_data["angle_usage"].items():
            percentage = (count / len(segments)) * 100
            f.write(f"{angle}: {count} clips ({percentage:.1f}%)\n")
        f.write("\n")
        
        # Sync information
        f.write("Synchronization Data:\n")
        f.write("-" * 20 + "\n")
        for angle, sync_info in project_data["sync_data"].items():
            offset = sync_info.get('offset', 0.0)
            timecode = sync_info.get('timecode', 'N/A')
            f.write(f"{angle}: offset {offset:.3f}s, timecode {timecode}\n")
        f.write("\n")
        
        # Timeline with angle switches
        f.write("Multicam Timeline:\n")
        f.write("-" * 20 + "\n")
        
        pos = 0
        for i, seg in enumerate(segments, 1):
            angle = seg.get("camera_angle", "unknown")
            f.write(f"{i:2d}. [{pos:5.1f}s] [{angle}] {seg['text'][:50]}...\n")
            f.write(f"    Source: {seg['source_video']} ({seg['start_time']:.1f}-{seg['end_time']:.1f}s)\n")
            pos += seg["duration"]


def _generate_multicam_premiere_xml(segments, camera_folders, sync_data, xml_path):
    """Generate Premiere Pro compatible multicam XML file."""
    
    # Collect all video files from all angles
    all_video_files = {}
    file_counter = 1
    
    for angle_name, folder_path in camera_folders.items():
        folder = Path(folder_path)
        
        # Get video files for this angle
        video_files = []
        for ext in ['.mp4', '.mov', '.mxf', '.avi', '.mkv']:
            video_files.extend(folder.glob(f"*{ext}"))
            video_files.extend(folder.glob(f"*{ext.upper()}"))
        
        for video_file in sorted(video_files):
            file_key = f"{angle_name}_{video_file.name}"
            all_video_files[file_key] = {
                'path': video_file,
                'angle': angle_name,
                'id': file_counter
            }
            file_counter += 1
    
    # Build XML using list approach to avoid string issues
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<xmeml version="5">',
        '  <project>',
        '    <name>AI Generated Multicam Edit</name>',
        '    <children>',
        '      <bin>',
        '        <name>Media</name>',
        '        <children>'
    ]
    
    # Add individual media files
    for file_key, file_info in all_video_files.items():
        video_path = file_info['path']
        file_id = file_info['id']
        video_name = video_path.name
        file_url = str(video_path.absolute()).replace("\\", "/")
        
        clip_xml = f'''          <clip id="clip{file_id}">
            <name>{video_name}</name>
            <duration>72000</duration>
            <rate>
              <timebase>24</timebase>
              <ntsc>FALSE</ntsc>
            </rate>
            <media>
              <video>
                <track>
                  <clipitem id="clipitem{file_id}">
                    <name>{video_name}</name>
                    <duration>72000</duration>
                    <rate>
                      <timebase>24</timebase>
                      <ntsc>FALSE</ntsc>
                    </rate>
                    <file id="file{file_id}">
                      <name>{video_name}</name>
                      <pathurl>file://localhost/{file_url}</pathurl>
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
        
        xml_lines.append(clip_xml)
    
    # Add multicam sequence structure
    sequence_lines = [
        '        </children>',
        '      </bin>',
        '      <sequence>',
        '        <name>Multicam Source</name>',
        '        <duration>72000</duration>',
        '        <rate>',
        '          <timebase>24</timebase>',
        '          <ntsc>FALSE</ntsc>',
        '        </rate>',
        '        <media>',
        '          <video>'
    ]
    xml_lines.extend(sequence_lines)
    
    # Add tracks for each camera angle
    for angle_idx, (angle_name, folder_path) in enumerate(camera_folders.items()):
        offset_frames = int(sync_data.get(angle_name, {}).get('offset', 0.0) * 24)
        
        track_lines = [
            '            <track>',
            '              <enabled>TRUE</enabled>',
            '              <locked>FALSE</locked>'
        ]
        xml_lines.extend(track_lines)
        
        # Find files for this angle and add them to the track
        angle_files = [f for f in all_video_files.values() if f['angle'] == angle_name]
        timeline_pos = offset_frames
        
        for file_info in sorted(angle_files, key=lambda x: x['path'].name):
            file_id = file_info['id']
            duration_frames = 72000  # Placeholder
            
            clip_xml = f'''              <clipitem id="multicam_{angle_name}_{file_id}">
                <name>{file_info['path'].name}</name>
                <duration>{duration_frames}</duration>
                <rate>
                  <timebase>24</timebase>
                  <ntsc>FALSE</ntsc>
                </rate>
                <start>{timeline_pos}</start>
                <end>{timeline_pos + duration_frames}</end>
                <in>0</in>
                <out>{duration_frames}</out>
                <file id="file{file_id}"/>
              </clipitem>'''
            
            xml_lines.append(clip_xml)
            timeline_pos += duration_frames
        
        xml_lines.append('            </track>')
    
    # Add timeline sequence
    timeline_lines = [
        '          </video>',
        '        </media>',
        '      </sequence>',
        '      <sequence>',
        '        <name>Multicam Timeline</name>',
        '        <duration>72000</duration>',
        '        <rate>',
        '          <timebase>24</timebase>',
        '          <ntsc>FALSE</ntsc>',
        '        </rate>',
        '        <media>',
        '          <video>',
        '            <track>'
    ]
    xml_lines.extend(timeline_lines)
    
    # Add timeline clips with angle switches
    timeline_pos = 0
    for i, seg in enumerate(segments):
        # Find the file for this segment
        source_file = None
        for file_key, file_info in all_video_files.items():
            if file_info['angle'] == seg['camera_angle'] and seg['source_video'] in file_key:
                source_file = file_info
                break
        
        if not source_file:
            logger.warning(f"Could not find source file for segment {i+1}")
            continue
        
        start_frame = int(seg["start_time"] * 24)
        end_frame = int(seg["end_time"] * 24)
        duration_frames = end_frame - start_frame
        timeline_start = int(timeline_pos * 24)
        timeline_end = timeline_start + duration_frames
        
        clip_name = f"{seg['source_video']} - {seg['camera_angle']}"
        angle_index = list(camera_folders.keys()).index(seg['camera_angle']) + 1
        
        clip_xml = f'''              <clipitem id="timeline_multicam_clip{i+1}">
                <name>{clip_name}</name>
                <duration>{duration_frames}</duration>
                <rate>
                  <timebase>24</timebase>
                  <ntsc>FALSE</ntsc>
                </rate>
                <start>{timeline_start}</start>
                <end>{timeline_end}</end>
                <in>{start_frame}</in>
                <out>{end_frame}</out>
                <file id="file{source_file['id']}"/>
                <sourcetrack>
                  <mediatype>video</mediatype>
                  <trackindex>{angle_index}</trackindex>
                </sourcetrack>
              </clipitem>'''
        
        xml_lines.append(clip_xml)
        timeline_pos += seg["duration"]
    
    # Add closing tags
    closing_lines = [
        '            </track>',
        '          </video>',
        '        </media>',
        '      </sequence>',
        '    </children>',
        '  </project>',
        '</xmeml>'
    ]
    xml_lines.extend(closing_lines)
    
    # Join all lines and save
    xml_content = '\n'.join(xml_lines)
    xml_path.write_text(xml_content, encoding='utf-8')


def _generate_premiere_xml(segments, video_dir, xml_path):
    """Generate Premiere Pro compatible XML file (single camera)."""
    
    # Get unique video files
    video_files = list({seg["source_video"] for seg in segments})
    
    # Start with XML header
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<xmeml version="5">',
        '  <project>',
        '    <name>AI Generated Edit</name>',
        '    <children>',
        '      <bin>',
        '        <name>Media</name>',
        '        <children>'
    ]
    
    # Add media files
    for i, video_file in enumerate(video_files):
        video_path = Path(video_dir) / video_file
        file_url = str(video_path.absolute()).replace("\\", "/")
        
        clip_xml = f'''          <clip id="clip{i+1}">
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
                      <pathurl>file://localhost/{file_url}</pathurl>
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
        
        xml_lines.append(clip_xml)
    
    # Add sequence header
    sequence_header = [
        '        </children>',
        '      </bin>',
        '      <sequence>',
        '        <name>AI Edit Timeline</name>',
        '        <duration>72000</duration>',
        '        <rate>',
        '          <timebase>24</timebase>',
        '          <ntsc>FALSE</ntsc>',
        '        </rate>',
        '        <media>',
        '          <video>',
        '            <track>'
    ]
    xml_lines.extend(sequence_header)
    
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
        
        clip_xml = f'''              <clipitem id="timeline_clip{i+1}">
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
        
        xml_lines.append(clip_xml)
        timeline_pos += seg["duration"]
    
    # Add closing tags
    closing_tags = [
        '            </track>',
        '          </video>',
        '        </media>',
        '      </sequence>',
        '    </children>',
        '  </project>',
        '</xmeml>'
    ]
    xml_lines.extend(closing_tags)
    
    # Join all lines and save
    xml_content = '\n'.join(xml_lines)
    xml_path.write_text(xml_content, encoding='utf-8')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test single camera XML building
    try:
        build_xml_project("temp/script.json", "input/videos", "output")
        print("Single camera XML test completed")
    except Exception as e:
        print(f"Single camera test failed: {e}")
    
    # Test multicam XML building (if you have test data)
    # try:
    #     test_sync_data = {
    #         "Camera_1": {"offset": 0.0, "timecode": "10:00:00:00"},
    #         "Camera_2": {"offset": 2.5, "timecode": "10:00:02:15"}
    #     }
    #     test_folders = {"Camera_1": "test/cam1", "Camera_2": "test/cam2"}
    #     build_multicam_xml_project("temp/script.json", test_folders, test_sync_data, "output")
    #     print("Multicam XML test completed")
    # except Exception as e:
    #     print(f"Multicam test failed: {e}")