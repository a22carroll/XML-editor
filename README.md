# AI Video Editor for DaVinci Resolve

An intelligent video editing tool that automatically generates and edits videos based on user prompts. Upload your video clips, describe what you want, and get a professionally edited DaVinci Resolve project.

## 🎯 How It Works

1. **Upload Videos + Prompt** → Place video files in `input/videos/` and describe your vision in `input/prompt.txt`
2. **Auto-Transcription** → AI generates timestamped transcripts from your videos
3. **Script Generation** → AI selects the best sentences from transcripts based on your prompt
4. **Video Assembly** → Creates a DaVinci Resolve project with precisely cut clips

## 🚀 Quick Start

### 1. Installation
```bash
# Clone or download this project
cd resolve_ai_editor

# Install dependencies
pip install -r requirements.txt

# Make sure DaVinci Resolve is installed and running
```

### 2. Setup Your Content
```bash
# Add your video files
cp your_videos.mp4 input/videos/

# Edit your prompt (describe what you want the video to convey)
nano input/prompt.txt
```

### 3. Run the Pipeline
```bash
python run.py
```

### 4. Open in DaVinci Resolve
The generated project file will be saved as `output/project.drp` - open this in DaVinci Resolve to see your automatically edited video!

## 📁 Project Structure

```
resolve_ai_editor/
├── input/                    # Your uploads
│   ├── videos/              # Video files (MP4, MOV, etc.)
│   └── prompt.txt           # What you want the video to convey
├── temp/                    # Generated during processing
│   ├── transcripts/         # Auto-generated transcripts
│   └── script.json         # AI-generated script
├── output/                  # Final results
│   ├── project.drp         # DaVinci Resolve project
│   └── final_video.mp4     # Optional rendered output
├── src/                     # Source code
│   ├── transcription.py    # Video → Transcripts
│   ├── script_generator.py # AI script generation
│   ├── resolve_builder.py  # DaVinci project creation
│   └── pipeline.py         # Main workflow
├── config.yaml             # Settings
├── requirements.txt        # Dependencies
├── run.py                  # Simple entry point
└── README.md              # This file
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **Transcription quality**: Change Whisper model size
- **AI models**: Switch embedding models for script generation
- **OpenAI integration**: Add API key for enhanced script refinement
- **Video settings**: Frame rate, quality, etc.

## 🎬 Example Usage

### Basic Example
```bash
# 1. Add videos to input/videos/
cp interview.mp4 input/videos/
cp broll.mp4 input/videos/

# 2. Create your prompt
echo "Create a 2-minute highlight reel focusing on the most inspiring and energetic moments" > input/prompt.txt

# 3. Run
python run.py

# 4. Open output/project.drp in DaVinci Resolve
```

### Advanced Example
```yaml
# config.yaml - for higher quality
transcription:
  model_size: "large"  # Better transcription accuracy

script_generation:
  openai_api_key: "your-key-here"  # Enhanced script flow
  target_length: "short"  # 30-60 second videos
```

## 🔧 Requirements

### Software
- **Python 3.8+**
- **DaVinci Resolve 18+** (free version works fine)
- **FFmpeg** (for video processing)

### Hardware
- **8GB+ RAM** recommended
- **GPU optional** but speeds up transcription significantly

## 🤝 Troubleshooting

### Common Issues

**"Could not connect to DaVinci Resolve"**
- Make sure DaVinci Resolve is running
- Enable external scripting in DaVinci Resolve preferences

**"No video files found"**
- Check that video files are in `input/videos/`
- Supported formats: MP4, MOV, AVI, MKV, WMV, FLV

**"Transcription is very slow"**
- Reduce Whisper model size in `config.yaml` (try "base" or "small")
- Consider using GPU acceleration

**"Script generation produces poor results"**
- Make your prompt more specific and detailed
- Add OpenAI API key for better script refinement
- Check that transcripts contain relevant dialogue

### Debug Mode
```bash
# Run with detailed logging
python run.py --debug
```

## 🔮 Advanced Features

### Custom AI Models
```yaml
# config.yaml
script_generation:
  embedding_model: "all-mpnet-base-v2"  # Higher quality embeddings
  openai_api_key: "your-key"            # GPT-powered refinement
```

### Batch Processing
```python
# Process multiple projects
from src.pipeline import VideoPipeline

for project_dir in ["project1", "project2", "project3"]:
    pipeline = VideoPipeline(f"{project_dir}/config.yaml")
    pipeline.run_full_pipeline()
```

## 📝 Tips for Best Results

### Writing Effective Prompts
- **Be specific**: "Create an upbeat product demo highlighting key features" vs "Make a good video"
- **Include tone**: "Professional and informative" or "Fun and energetic"
- **Specify length**: "Create a 90-second highlight reel"
- **Mention key themes**: "Focus on customer testimonials and success stories"

### Video Selection
- **Clear audio** produces better transcripts
- **Good content variety** gives AI more options
- **Consistent quality** across clips works better
- **Avoid background music** during transcription (can interfere)

## 🚀 What's Next?

This is just the beginning! Potential enhancements:
- **Multi-language support** for global content
- **Advanced video effects** and automated color correction
- **Music integration** with AI-powered soundtrack selection
- **Speaker identification** for multi-person interviews
- **Visual scene analysis** for better B-roll selection
- **Template system** for different video styles (corporate, social media, documentary)
- **Real-time preview** during script generation
- **Collaborative editing** with team review workflows

## 📄 License

MIT License - feel free to modify and distribute

## 🤝 Contributing

Contributions welcome! Areas where help is needed:
- **Video format support** (more codecs, containers)
- **AI model improvements** (better embeddings, local LLMs)
- **UI development** (web interface, desktop app)
- **Performance optimization** (parallel processing, caching)
- **Documentation** (tutorials, examples)

## 💬 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Share your creations and get help from the community
- **Documentation**: Check the `/docs` folder for detailed guides

---

**Made with ❤️ for content creators who want to focus on storytelling, not tedious editing.**