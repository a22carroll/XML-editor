import logging
from pathlib import Path
from dotenv import load_dotenv

from src.transcription import transcribe_videos
from src.script_generator import generate_script, generate_multicam_script  # NEW import
from src.xml_builder import build_xml_project, build_multicam_xml_project  # NEW import
from src.timecode_utils import get_multicam_sync_data  # NEW import

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


def run_pipeline(video_path, prompt_text, output_path, duration_limit=None, max_sentences=15, is_multicam=False):
    """Run the complete XML editing pipeline using GPT-4o with optional multicam support."""
    
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Create directories
        Path("temp/transcripts").mkdir(parents=True, exist_ok=True)
        Path(output_path).mkdir(parents=True, exist_ok=True)

        logger.info("Starting XML AI Editor pipeline")
        mode_text = "Multicam" if is_multicam else "Single camera"
        logger.info(f"Mode: {mode_text}")

        # Step 1: Transcribe videos
        logger.info("Step 1: Transcribing videos...")
        
        if is_multicam:
            # Multicam transcription
            if not isinstance(video_path, dict):
                raise ValueError("Multicam mode requires dictionary of camera angles")
            
            # Get sync data first
            sync_data = get_multicam_sync_data(video_path)
            logger.info(f"Multicam sync data calculated for {len(sync_data)} angles")
            
            # Transcribe each camera angle
            angle_transcripts = {}
            for angle_name, folder_path in video_path.items():
                logger.info(f"Transcribing angle: {angle_name}")
                transcripts = transcribe_videos(
                    input_dir=folder_path,
                    output_dir=f"temp/transcripts/{angle_name}",
                    model_size="base"
                )
                angle_transcripts[angle_name] = transcripts
            
            # Check if we got any transcripts
            total_transcripts = sum(len(transcripts) for transcripts in angle_transcripts.values())
            if total_transcripts == 0:
                logger.error("Multicam transcription failed - no transcript files generated")
                return False
            
            logger.info(f"Multicam transcription complete - {len(angle_transcripts)} angles, {total_transcripts} total files")
            transcript_data = {'angles': angle_transcripts, 'sync_data': sync_data}
            
        else:
            # Single camera transcription (existing logic)
            transcript_files = transcribe_videos(
                input_dir=video_path,
                output_dir="temp/transcripts",
                model_size="base"
            )

            if not transcript_files:
                logger.error("Transcription failed - no transcript files generated")
                return False

            logger.info(f"Transcription complete - {len(transcript_files)} files processed")
            transcript_data = transcript_files

        # Step 2: Generate script with GPT-4o
        logger.info("Step 2: Generating script with GPT-4o...")
        
        if is_multicam:
            script_file = generate_multicam_script(
                angle_transcripts=transcript_data['angles'],
                sync_data=transcript_data['sync_data'],
                prompt_text=prompt_text,
                output_file="temp/script.json",
                max_sentences=max_sentences,
                target_duration=duration_limit
            )
        else:
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
        
        if is_multicam:
            success = build_multicam_xml_project(
                script_file=script_file,
                camera_folders=video_path,
                sync_data=transcript_data['sync_data'],
                output_dir=output_path
            )
        else:
            success = build_xml_project(
                script_file=script_file,
                video_dir=video_path,
                output_dir=output_path
            )

        if success:
            logger.info(f"Pipeline completed successfully - {mode_text} XML project ready for import")
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