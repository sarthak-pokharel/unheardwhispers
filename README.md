# Script to Subtitles Converter

A Streamlit application that creates SRT subtitle files by aligning video speech with your script text. This app uses OpenAI's Whisper for speech recognition and text alignment algorithms to match the transcript timing with your exact script dialog.

## Features

- **Upload Video Files**: Support for MP4, AVI, MOV, and MKV formats
- **Script Input**: Upload script files or paste script text directly
- **Exact Text Matching**: Maintains the exact wording from your script
- **Character Names**: Option to include or exclude character names in subtitles
- **Customizable Settings**: Adjust similarity thresholds and chunking parameters
- **Interactive UI**: Real-time progress tracking and results visualization
- **SRT Download**: Download ready-to-use SRT subtitle files

## Requirements

- Python 3.8 or later
- FFmpeg (required for audio processing)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd script-to-subtitles
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install FFmpeg (if not already installed):

   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## Usage

1. Start the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501)

3. Use the interface to:
   - Upload your video file
   - Upload or paste your script
   - Adjust settings in the sidebar
   - Click "Generate Subtitles"
   - Download the resulting SRT file

## Script Format

Your script should follow this format:

```
CHARACTER: Dialog text.

ANOTHER CHARACTER: More dialog text.
```

## How It Works

1. **Audio Extraction**: Extracts audio from the uploaded video file
2. **Speech Recognition**: Uses Whisper to detect speech segments and their timing
3. **Script Parsing**: Extracts dialog lines from the provided script
4. **Text Chunking**: Breaks down dialog into manageable segments
5. **Alignment**: Matches Whisper speech segments with script chunks
6. **SRT Generation**: Creates subtitles using the exact script text with aligned timing

## Advanced Settings

- **Whisper Model Size**: Choose between tiny, base, small, medium, or large models (larger models are more accurate but slower)
- **Similarity Threshold**: Adjust the minimum similarity score required for matching
- **Max Words Per Chunk**: Control how dialog lines are chunked for better alignment

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Streamlit](https://streamlit.io/) for the web interface
- [Pysrt](https://github.com/byroot/pysrt) for SRT file handling 