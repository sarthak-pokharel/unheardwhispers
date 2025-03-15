# Script to Subtitles Converter

A Streamlit application that creates SRT subtitle files by aligning video speech with your script text. This app uses OpenAI's Whisper for speech recognition and text alignment algorithms to match the transcript timing with your exact script dialog.

## Features

- **Upload Video Files**: Support for MP4, AVI, MOV, and MKV formats
- **Script Input**: Upload script files or paste script text directly (optional)
- **Exact Text Matching**: Maintains the exact wording from your script
- **Character Names**: Option to include or exclude character names in subtitles
- **Whisper-Only Mode**: Can use Whisper's transcription directly without a script
- **Customizable Settings**: Adjust similarity thresholds and chunking parameters
- **Interactive UI**: Real-time progress tracking and results visualization
- **SRT Download**: Download ready-to-use SRT subtitle files

## Requirements

- Python 3.8 or later
- FFmpeg (required for audio processing)

## Quick Installation (Recommended)

The easiest way to install and run the application is using our setup script, which will:
- Check and install FFmpeg if needed
- Install all Python dependencies
- Create launcher scripts (runapp.bat/runapp.sh)

```bash
# Clone the repository (or download and extract the ZIP)
git clone https://github.com/sarthak-pokharel/unheardwhispers.git
cd script-to-subtitles

# Run the setup script
python setup.py
```

After setup completes, run the application with:
```bash
# On Windows:
runapp.bat

# On macOS/Linux:
./runapp.sh

# Or directly with Streamlit:
streamlit run src/app.py
```

## Manual Installation

If you prefer to install manually:

1. Ensure Python 3.8+ is installed
2. Install FFmpeg:
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` (or use your distro's package manager)
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   streamlit run src/app.py
   ```

## Usage

1. Start the application using one of the methods above
2. Use the interface to:
   - Upload your video file
   - Choose whether to use script matching or direct Whisper transcription
   - If using script matching, upload or paste your script
   - Adjust settings in the sidebar
   - Click "Generate Subtitles"
   - Download the resulting SRT file

## Finding Transcripts

When using script matching mode, you'll need a transcript of your video. Here are some places to find transcripts:

- [Forever Dreaming Transcripts](http://transcripts.foreverdreaming.org/) - Transcripts for many TV shows
- [TVSubtitles.net](http://www.tvsubtitles.net/) - TV show subtitle/script resources
- [Subscene](https://subscene.com/) - Community-contributed subtitles
- [Springfield! Springfield!](https://www.springfieldspringfield.co.uk/) - Movie and TV scripts
- Official screenplays or shooting scripts for movies
- Fan-created transcripts on wikis for popular shows

## Script Format

When using script matching, your script should follow this format:

```
CHARACTER: Dialog text.

ANOTHER CHARACTER: More dialog text.
```

## How It Works

1. **Audio Extraction**: Extracts audio from the uploaded video file
2. **Speech Recognition**: Uses Whisper to detect speech segments and their timing
3. **Processing Mode**:
   - **With Script**: Extracts dialog from script, matches with speech segments
   - **Without Script**: Uses Whisper's transcription directly
4. **SRT Generation**: Creates subtitles with proper timing information

## Advanced Settings

- **Whisper Model Size**: Choose between tiny, base, small, medium, or large models
- **Similarity Threshold**: When using script matching, adjust matching sensitivity
- **Max Words Per Chunk**: Control how dialog lines are chunked for better alignment

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Streamlit](https://streamlit.io/) for the web interface
- [Pysrt](https://github.com/byroot/pysrt) for SRT file handling 