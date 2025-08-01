"""
AI-based script generator using OpenAI GPT-4o for intelligent content selection.
Enhanced with multicam support - SIMPLIFIED VERSION.
"""

import json
import logging
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()
logger = logging.getLogger(__name__)


def generate_script(prompt_text: str, transcript_dir: str, output_file: str, 
                   max_sentences: int = 15, target_duration: float = None, temperature: float = 0.3):
    """Generate editing script using GPT-4o to select and arrange content (single camera)."""
    
    client = OpenAI()
    prompt = prompt_text.strip()
    
    if not prompt:
        raise ValueError("Prompt is empty")
    
    # Load sentences from all transcript files
    all_sentences = []
    for file in Path(transcript_dir).glob("*.json"):
        data = json.load(file.open())
        for sent in data.get("sentences", []):
            sent["source_video"] = data.get("video_file", "unknown")
            all_sentences.append(sent)
    
    if not all_sentences:
        raise RuntimeError("No sentences found")
    
    logger.info(f"Loaded {len(all_sentences)} sentences")
    
    # Prepare content for GPT-4o
    sentences_text = "\n".join(
        f"[{i}] {s['text']} (Duration: {s['duration']:.1f}s, Source: {s['source_video']})"
        for i, s in enumerate(all_sentences)
    )
    
    constraint = f" Target duration: {target_duration}s." if target_duration else f" Max {max_sentences} sentences."
    
    gpt_prompt = f"""Create a compelling video script from available content.

REQUEST: {prompt}

CONTENT:
{sentences_text}

Select relevant sentence indices (numbers in brackets) considering narrative flow, impact, and timing.{constraint}

Return JSON only:
{{"selected_indices": [1, 5, 12, ...], "reasoning": "Brief explanation"}}"""

    # Call GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Expert video editor focused on storytelling."},
            {"role": "user", "content": gpt_prompt}
        ],
        temperature=temperature,
        max_tokens=1000
    )
    
    # Parse response
    gpt_response = response.choices[0].message.content.strip()
    
    # Extract JSON
    if "```json" in gpt_response:
        start = gpt_response.find("```json") + 7
        end = gpt_response.find("```", start)
        json_str = gpt_response[start:end].strip()
    elif "{" in gpt_response:
        start = gpt_response.find("{")
        end = gpt_response.rfind("}") + 1
        json_str = gpt_response[start:end]
    else:
        json_str = gpt_response
    
    try:
        selection_data = json.loads(json_str)
        selected_indices = selection_data.get("selected_indices", [])
        reasoning = selection_data.get("reasoning", "No reasoning")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response: {gpt_response}")
        raise RuntimeError("GPT-4o response was not valid JSON")
    
    # Validate and build script
    valid_indices = [i for i in selected_indices if 0 <= i < len(all_sentences)]
    if not valid_indices:
        raise RuntimeError("No valid sentences selected")
    
    selected_sentences = [all_sentences[i] for i in valid_indices]
    total_duration = sum(s["duration"] for s in selected_sentences)
    
    script = {
        "prompt": prompt,
        "gpt4_reasoning": reasoning,
        "total_sentences": len(selected_sentences),
        "estimated_duration": total_duration,
        "segments": [
            {
                "sequence": i + 1,
                "text": s["text"],
                "start_time": s["start"],
                "end_time": s["end"],
                "duration": s["duration"],
                "source_video": s["source_video"]
            }
            for i, s in enumerate(selected_sentences)
        ]
    }
    
    # Save script
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(json.dumps(script, indent=2, ensure_ascii=False))
    
    logger.info(f"Saved {len(selected_sentences)} sentences ({total_duration:.1f}s) to {output_file}")
    return output_file


def generate_multicam_script(angle_transcripts: Dict[str, List], sync_data: Dict, prompt_text: str, 
                           output_file: str, max_sentences: int = 15, target_duration: float = None, 
                           temperature: float = 0.3):
    """Generate multicam editing script - SIMPLIFIED approach."""
    
    client = OpenAI()
    prompt = prompt_text.strip()
    
    if not prompt:
        raise ValueError("Prompt is empty")
    
    # SIMPLIFIED: Create separate lists for each angle, don't merge timestamps
    angle_content = {}
    total_sentences = 0
    
    for angle_name, transcript_files in angle_transcripts.items():
        angle_sentences = []
        
        for file in transcript_files:
            data = json.load(file.open())
            for sent in data.get("sentences", []):
                sent["source_video"] = data.get("video_file", "unknown")
                sent["camera_angle"] = angle_name
                angle_sentences.append(sent)
        
        angle_content[angle_name] = angle_sentences
        total_sentences += len(angle_sentences)
        logger.info(f"Angle {angle_name}: {len(angle_sentences)} sentences")
    
    if total_sentences == 0:
        raise RuntimeError("No sentences found in any camera angle")
    
    logger.info(f"Total: {total_sentences} sentences from {len(angle_content)} angles")
    
    # Build content for GPT-4o - organize by angle for clarity
    content_by_angle = []
    sentence_index = 0
    index_to_sentence = {}  # Map global index to actual sentence data
    
    for angle_name, sentences in angle_content.items():
        if not sentences:
            continue
            
        content_by_angle.append(f"\n=== {angle_name.upper()} ===")
        
        for sent in sentences:
            content_by_angle.append(
                f"[{sentence_index}] {sent['text']} "
                f"(Duration: {sent['duration']:.1f}s, Source: {sent['source_video']}, "
                f"Time: {sent['start']:.1f}-{sent['end']:.1f}s)"
            )
            
            # Store the mapping
            index_to_sentence[sentence_index] = {
                **sent,  # Include all original data
                "camera_angle": angle_name
            }
            sentence_index += 1
    
    content_text = "\n".join(content_by_angle)
    
    # Create sync info summary
    sync_summary = []
    for angle, sync_info in sync_data.items():
        offset = sync_info.get('offset', 0.0)
        timecode = sync_info.get('timecode', 'N/A')
        sync_summary.append(f"• {angle}: {timecode} (offset: {offset:.3f}s)")
    
    constraint = f" Target duration: {target_duration}s." if target_duration else f" Max {max_sentences} sentences."
    
    gpt_prompt = f"""Create a dynamic multicam video edit from synchronized camera angles.

REQUEST: {prompt}

CAMERA SYNC INFO:
{chr(10).join(sync_summary)}

CONTENT BY CAMERA ANGLE:
{content_text}

Create an engaging edit by:
1. Selecting sentence indices [numbers in brackets] from any angle
2. Mixing angles for visual variety and storytelling impact
3. Consider: wide shots for context, close-ups for emotion, angle changes for energy{constraint}

Return JSON only:
{{
  "selected_indices": [1, 15, 23, 8, ...],
  "reasoning": "Brief explanation of content and angle choices"
}}"""

    # Call GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Expert multicam video editor. Select diverse angles for dynamic storytelling."},
            {"role": "user", "content": gpt_prompt}
        ],
        temperature=temperature,
        max_tokens=1500
    )
    
    # Parse response
    gpt_response = response.choices[0].message.content.strip()
    
    # Extract JSON
    if "```json" in gpt_response:
        start = gpt_response.find("```json") + 7
        end = gpt_response.find("```", start)
        json_str = gpt_response[start:end].strip()
    elif "{" in gpt_response:
        start = gpt_response.find("{")
        end = gpt_response.rfind("}") + 1
        json_str = gpt_response[start:end]
    else:
        json_str = gpt_response
    
    try:
        selection_data = json.loads(json_str)
        selected_indices = selection_data.get("selected_indices", [])
        reasoning = selection_data.get("reasoning", "No reasoning")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response: {gpt_response}")
        raise RuntimeError("GPT-4o response was not valid JSON")
    
    # Build multicam script using the index mapping
    valid_indices = [i for i in selected_indices if i in index_to_sentence]
    if not valid_indices:
        raise RuntimeError("No valid sentences selected")
    
    selected_sentences = []
    for idx in valid_indices:
        sentence_data = index_to_sentence[idx]
        selected_sentences.append(sentence_data)
    
    total_duration = sum(s["duration"] for s in selected_sentences)
    
    # Count angle usage
    angle_usage = {}
    for s in selected_sentences:
        angle = s["camera_angle"]
        angle_usage[angle] = angle_usage.get(angle, 0) + 1
    
    # Build multicam script
    script = {
        "type": "multicam",
        "prompt": prompt,
        "gpt4_reasoning": reasoning,
        "total_sentences": len(selected_sentences),
        "estimated_duration": total_duration,
        "camera_angles": list(angle_content.keys()),
        "angle_usage": angle_usage,
        "sync_data": sync_data,
        "segments": [
            {
                "sequence": i + 1,
                "text": s["text"],
                "start_time": s["start"],
                "end_time": s["end"],
                "duration": s["duration"],
                "source_video": s["source_video"],
                "camera_angle": s["camera_angle"]
            }
            for i, s in enumerate(selected_sentences)
        ]
    }
    
    # Save script
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(json.dumps(script, indent=2, ensure_ascii=False))
    
    logger.info(f"Saved multicam script: {len(selected_sentences)} segments ({total_duration:.1f}s)")
    logger.info(f"Angle usage: {angle_usage}")
    
    return output_file


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_script(
        "Create an exciting highlight reel with energetic moments",
        "temp/transcripts",
        "temp/script.json",
        target_duration=60
    )