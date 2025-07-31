import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from src.transcription import transcribe_videos
from src.script_generator import generate_script
from src.resolve_builder import build_resolve_project

load_dotenv()


def setup_logging():
    Path("output/logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("output/logs/pipeline.log"),
            logging.StreamHandler()
        ]
    )


def run_pipeline(video_path, prompt_text, output_path, duration_limit=None, max_sentences=15):
    """Run the complete video editing pipeline using GPT-4o."""
    
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Create directories
        Path("temp/transcripts").mkdir(parents=True, exist_ok=True)
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Step 1: Transcribe videos
        transcript_files = transcribe_videos(
            input_dir=video_path,
            output_dir="temp/transcripts",
            model_size="base"
        )

        if not transcript_files:
            logger.error("❌ Transcription failed")
            return False

        # Step 2: Generate script with GPT-4o
        script_file = generate_script(
            prompt_text=prompt_text,
            transcript_dir="temp/transcripts",
            output_file="temp/script.json",
            max_sentences=max_sentences,
            target_duration=duration_limit
        )

        # Step 3: Build Resolve project
        success = build_resolve_project(
            script_file=script_file,
            video_dir=video_path,
            output_dir=output_path
        )

        if success:
            logger.info("✅ Pipeline completed successfully")
        else:
            logger.error("❌ Resolve build failed")
            
        return success

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    run_pipeline()