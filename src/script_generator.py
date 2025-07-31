"""
AI-based script generator using OpenAI GPT-4o for intelligent content selection.
"""

import json
import logging
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def generate_script(prompt_text: str, transcript_dir: str, output_file: str, 
                   max_sentences: int = 15, target_duration: float = None, temperature: float = 0.3):
    """Generate editing script using GPT-4o to select and arrange content."""
    
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_script(
        "Create an exciting highlight reel with energetic moments",
        "temp/transcripts",
        "temp/script.json",
        target_duration=60
    )