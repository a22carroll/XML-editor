import logging
from pathlib import Path
from dotenv import load_dotenv

from src.transcription import transcribe_videos
from src.script_generator import generate_script
from src.xml_builder import build_xml_project

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
    """Run the complete XML editing pipeline using GPT-4o."""
    
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Create directories
        Path("temp/transcripts").mkdir(parents=True, exist_ok=True)
        Path(output_path).mkdir(parents=True, exist_ok=True)

        logger.info("Starting XML AI Editor pipeline")

        # Step 1: Transcribe videos
        logger.info("Step 1: Transcribing videos...")
        transcript_files = transcribe_videos(
            input_dir=video_path,
            output_dir="temp/transcripts",
            model_size="base"
        )

        if not transcript_files:
            logger.error("Transcription failed - no transcript files generated")
            return False

        logger.info(f"Transcription complete - {len(transcript_files)} files processed")

        # Step 2: Generate script with GPT-4o
        logger.info("Step 2: Generating script with GPT-4o...")
        script_file = generate_script(
            prompt_text=prompt_text,
            transcript_dir="temp/transcripts",
            output_file="temp/script.json",
            max_sentences=max_sentences,
            target_duration=duration_limit
        )

        logger.info("Script generation complete")

        # Step 3: Build XML project
        logger.info("Step 3: Building XML project...")
        success = build_xml_project(
            script_file=script_file,
            video_dir=video_path,
            output_dir=output_path
        )

        if success:
            logger.info("Pipeline completed successfully - XML project ready for import")
            return True
        else:
            logger.error("XML build failed")
            return False

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    run_pipeline()