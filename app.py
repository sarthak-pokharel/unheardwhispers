import streamlit as st
import os
import tempfile
import time
import pandas as pd
from pydub import AudioSegment
import whisper
import pysrt
import re
import nltk
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import base64
from io import StringIO
import plotly.express as px

# Download NLTK resources (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Set page config
st.set_page_config(
    page_title="Script to Subtitles",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #424242;
    }
    .info-text {
        font-size: 1rem;
        color: #616161;
    }
    .highlight {
        background-color: #f0f7ff;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #1E88E5;
    }
    .success-box {
        background-color: #e6f4ea;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #34a853;
    }
    .stProgress > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions from the original script
def extract_audio_from_video(video_file_path, audio_file_path, progress_callback=None):
    """Extract audio from video file."""
    try:
        video = AudioSegment.from_file(video_file_path)
        video.export(audio_file_path, format="mp3")
        if progress_callback:
            progress_callback("Audio extracted successfully", 0.2)
        return True
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error extracting audio: {e}", 0.2, error=True)
        return False

def convert_audio_to_wav(audio_file_path, temp_wav_path, progress_callback=None):
    """Convert audio to WAV format for Whisper processing."""
    try:
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(temp_wav_path, format="wav")
        if progress_callback:
            progress_callback("Audio converted to WAV format", 0.3)
        return True
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error converting audio to WAV: {e}", 0.3, error=True)
        return False

def extract_dialog_from_script(script_content, progress_callback=None):
    """Extract all dialog lines from the script content, preserving exact text."""
    try:
        dialog_lines = []
        
        # Improved regex pattern for dialog extraction
        dialog_pattern = re.compile(r'([A-Z]+(?:\s[A-Z]+)*)(?:\s\([^)]*\))?:\s*(.*?)(?=\n\n|\n[A-Z]+(?:\s[A-Z]+)*(?:\s\([^)]*\))?:|\Z)', re.DOTALL)
        
        matches = dialog_pattern.findall(script_content)
        for character, text in matches:
            # Clean up the text (remove newlines but preserve exact words)
            clean_text = re.sub(r'\n\s*', ' ', text.strip())
            if clean_text:
                dialog_lines.append({
                    'character': character.strip(),
                    'text': clean_text
                })
        
        if progress_callback:
            progress_callback(f"Found {len(dialog_lines)} dialog lines in script", 0.4)
        
        return dialog_lines
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error extracting dialog from script: {e}", 0.4, error=True)
        return []

def chunk_sentence(sentence, character, max_words=10):
    """Break a sentence into smaller chunks based on punctuation and word count."""
    if len(sentence.split()) <= max_words:
        return [{
            'character': character,
            'text': sentence
        }]
    
    # Split by punctuation
    phrases = re.split(r'[,;()]', sentence)
    phrases = [p.strip() for p in phrases if p.strip()]
    
    if len(phrases) > 1:
        return [{'character': character, 'text': phrase} for phrase in phrases if phrase]
    
    # If no good punctuation breaks, try splitting by word count
    words = sentence.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk_words = words[i:i+max_words]
        if chunk_words:
            chunks.append({
                'character': character,
                'text': ' '.join(chunk_words)
            })
    
    return chunks

def break_dialog_into_chunks(dialog_lines, max_words=10, progress_callback=None):
    """Break dialog lines into smaller chunks for more precise matching."""
    chunks = []
    
    for line in dialog_lines:
        character = line['character']
        text = line['text']
        
        # Use NLTK to split into sentences
        sentences = nltk.sent_tokenize(text)
        
        for sentence in sentences:
            chunks.extend(chunk_sentence(sentence, character, max_words))
    
    if progress_callback:
        progress_callback(f"Created {len(chunks)} script chunks from {len(dialog_lines)} dialog lines", 0.5)
    
    return chunks

def get_whisper_segments_with_text(temp_wav_path, model, progress_callback=None):
    """Get timing and transcribed text from Whisper for matching purposes."""
    try:
        if progress_callback:
            progress_callback("Transcribing audio with Whisper...", 0.6, intermediate=True)
        
        start_time = time.time()
        result = model.transcribe(temp_wav_path, task="transcribe")
        elapsed = time.time() - start_time
        
        segments = []
        for segment in result['segments']:
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'transcribed_text': segment['text'].strip()
            })
        
        if progress_callback:
            progress_callback(f"Transcription completed in {elapsed:.2f} seconds - Found {len(segments)} segments", 0.7)
        
        return segments
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error transcribing audio: {e}", 0.7, error=True)
        return []

def similarity_score(text1, text2):
    """Calculate similarity between two text strings."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def process_segment_matching(args):
    """Process a single segment matching for parallel execution."""
    segment, script_chunks, used_chunks, threshold = args
    transcribed_text = segment['transcribed_text'].lower()
    best_chunk = None
    best_score = 0
    best_index = -1
    
    # Find the best matching chunk for this segment
    for i, chunk in enumerate(script_chunks):
        if i in used_chunks:
            continue  # Skip already used chunks
            
        chunk_text = chunk['text'].lower()
        
        # Calculate similarity between transcribed text and chunk
        score = similarity_score(transcribed_text, chunk_text)
        
        if score > best_score:
            best_score = score
            best_chunk = chunk
            best_index = i
    
    return {
        'segment': segment,
        'best_chunk': best_chunk,
        'best_score': best_score,
        'best_index': best_index,
        'threshold': threshold
    }

def align_script_chunks_with_segments(script_chunks, whisper_segments, threshold=0.3, max_workers=4, progress_callback=None):
    """Align script chunks with Whisper segments by finding best matches."""
    aligned_segments = []
    used_chunks = set()
    
    # Prepare arguments for parallel processing
    args_list = [(segment, script_chunks, used_chunks, threshold) for segment in whisper_segments]
    
    if progress_callback:
        progress_callback(f"Aligning {len(whisper_segments)} segments with {len(script_chunks)} script chunks...", 0.75, intermediate=True)
    
    # Process in batches to update used_chunks
    for i in range(0, len(args_list), max_workers):
        batch = args_list[i:i+max_workers]
        
        # Process batch
        with ThreadPoolExecutor(max_workers=min(max_workers, len(batch))) as executor:
            results = list(executor.map(process_segment_matching, batch))
        
        # Process results in order
        for result in results:
            segment = result['segment']
            best_chunk = result['best_chunk']
            best_score = result['best_score']
            best_index = result['best_index']
            
            if best_chunk and best_score > threshold:
                # Found a good match
                if best_index not in used_chunks:
                    used_chunks.add(best_index)
                    aligned_segments.append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': best_chunk['text'],  # Exact text from script
                        'character': best_chunk['character'],
                        'match_score': best_score
                    })
                else:
                    # Already used, find next best
                    next_chunk = None
                    for i, chunk in enumerate(script_chunks):
                        if i not in used_chunks:
                            used_chunks.add(i)
                            next_chunk = chunk
                            break
                    
                    if next_chunk:
                        aligned_segments.append({
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': next_chunk['text'],
                            'character': next_chunk['character'],
                            'match_score': 0
                        })
            else:
                # If no good match, find the next unused chunk in sequence
                for i, chunk in enumerate(script_chunks):
                    if i not in used_chunks:
                        used_chunks.add(i)
                        aligned_segments.append({
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': chunk['text'],  # Exact text from script
                            'character': chunk['character'],
                            'match_score': 0
                        })
                        break
    
    if progress_callback:
        progress_callback(f"Created {len(aligned_segments)} aligned segments", 0.8)
    
    return aligned_segments

def generate_srt_from_segments(segments, include_character=True, progress_callback=None):
    """Generate SRT file content from aligned segments."""
    srt_subs = pysrt.SubRipFile()
    
    for i, segment in enumerate(segments):
        start_time = segment['start']
        end_time = segment['end']
        
        # Use exact text from the script file
        if include_character and segment.get('character'):
            text = f"{segment['character']}: {segment['text']}"
        else:
            text = segment['text']
        
        item = pysrt.SubRipItem(
            index=i + 1,
            start=pysrt.SubRipTime.from_ordinal(int(start_time * 1000)),
            end=pysrt.SubRipTime.from_ordinal(int(end_time * 1000)),
            text=text
        )
        srt_subs.append(item)
    
    # Create a string buffer
    srt_buffer = StringIO()
    srt_subs.write_into(srt_buffer)
    srt_content = srt_buffer.getvalue()
    
    if progress_callback:
        progress_callback("SRT file generated successfully", 0.9)
    
    return srt_content

def process_files(video_file, script_content, include_character=True, model_size="base", similarity_threshold=0.3, max_words=10, progress_callback=None):
    """Main processing function that handles the entire workflow."""
    # Create temporary directory for processing files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup file paths
        video_path = os.path.join(temp_dir, "input_video")
        audio_path = os.path.join(temp_dir, "extracted_audio.mp3")
        temp_wav_path = os.path.join(temp_dir, "temp.wav")
        
        # Write video file to disk
        with open(video_path, 'wb') as f:
            f.write(video_file.read())
        
        # Reset video file pointer
        video_file.seek(0)
        
        start_time = time.time()
        
        # Load Whisper model
        if progress_callback:
            progress_callback(f"Loading Whisper model ({model_size})...", 0.1)
        model = whisper.load_model(model_size)
        
        # Extract audio from video
        if not extract_audio_from_video(video_path, audio_path, progress_callback):
            return None
        
        # Convert to WAV format
        if not convert_audio_to_wav(audio_path, temp_wav_path, progress_callback):
            return None
        
        # Extract dialog lines from script
        dialog_lines = extract_dialog_from_script(script_content, progress_callback)
        if not dialog_lines:
            if progress_callback:
                progress_callback("No dialog found in script file", 0.4, error=True)
            return None
        
        # Break dialog lines into smaller chunks
        script_chunks = break_dialog_into_chunks(dialog_lines, max_words, progress_callback)
        
        # Get timing segments and transcribed text from Whisper
        whisper_segments = get_whisper_segments_with_text(temp_wav_path, model, progress_callback)
        if not whisper_segments:
            if progress_callback:
                progress_callback("No speech segments detected", 0.7, error=True)
            return None
        
        # Align script chunks with Whisper segments
        aligned_segments = align_script_chunks_with_segments(
            script_chunks, 
            whisper_segments, 
            threshold=similarity_threshold, 
            progress_callback=progress_callback
        )
        
        # Generate SRT file
        srt_content = generate_srt_from_segments(aligned_segments, include_character, progress_callback)
        
        # Final progress update
        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(f"Processing complete! Total time: {elapsed:.2f} seconds", 1.0)
        
        return {
            "srt_content": srt_content,
            "aligned_segments": aligned_segments,
            "stats": {
                "processing_time": elapsed,
                "dialog_lines": len(dialog_lines),
                "script_chunks": len(script_chunks),
                "speech_segments": len(whisper_segments),
                "subtitle_segments": len(aligned_segments)
            }
        }

def get_download_link(content, filename, text):
    """Generate a download link for a file."""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}" class="download-button">{text}</a>'
    return href

# Main UI
def main():
    # Header
    st.markdown('<p class="main-header">🎬 Script to Subtitles Converter</p>', unsafe_allow_html=True)
    st.markdown('<p class="info-text">Create accurate SRT subtitles from video and script files</p>', unsafe_allow_html=True)
    
    # Sidebar for options
    with st.sidebar:
        st.markdown('<p class="sub-header">Configuration</p>', unsafe_allow_html=True)
        
        model_size = st.selectbox(
            "Whisper Model Size", 
            options=["tiny", "base", "small", "medium", "large"],
            index=1,
            help="Larger models are more accurate but slower and use more memory"
        )
        
        include_character = st.checkbox(
            "Include Character Names", 
            value=True,
            help="Include character names in the subtitles (e.g., 'DOCTOR: Don't blink')"
        )
        
        similarity_threshold = st.slider(
            "Similarity Threshold", 
            min_value=0.1, 
            max_value=0.9, 
            value=0.3, 
            step=0.05,
            help="Minimum similarity score required to match transcribed text with script lines"
        )
        
        max_words = st.slider(
            "Max Words Per Chunk", 
            min_value=5, 
            max_value=20, 
            value=10, 
            step=1,
            help="Maximum words per chunk when breaking down long sentences"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This app creates SRT subtitle files by aligning video speech with your script text.
        It uses OpenAI's Whisper for speech recognition and text alignment algorithms to match
        the transcript timing with your exact script dialog.
        """)

    # Main content area - Two columns layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown('<p class="sub-header">📤 Upload Files</p>', unsafe_allow_html=True)
        
        video_file = st.file_uploader("Upload Video File", type=['mp4', 'avi', 'mov', 'mkv'])
        
        script_tab1, script_tab2 = st.tabs(["Upload Script File", "Paste Script Text"])
        
        with script_tab1:
            script_file = st.file_uploader("Upload Script File", type=['txt'])
            script_content = script_file.getvalue().decode('utf-8') if script_file else None
        
        with script_tab2:
            pasted_script = st.text_area(
                "Paste your script here", 
                height=300,
                placeholder="Paste your script text here. Format should be:\n\nCHARACTER: Dialog text.\n\nANOTHER CHARACTER: More dialog text."
            )
            if pasted_script and not script_content:
                script_content = pasted_script
        
        # Process button
        if video_file and script_content:
            process_button = st.button("Generate Subtitles", type="primary", use_container_width=True)
        else:
            st.warning("Please upload both a video file and script file (or paste script text) to continue.")
            process_button = False
    
    with col2:
        st.markdown('<p class="sub-header">ℹ️ Instructions</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="highlight">', unsafe_allow_html=True)
        st.markdown("""
        1. **Upload your video file** (MP4, AVI, MOV, etc.)
        2. **Provide your script** (upload TXT file or paste text)
        3. **Adjust settings** in the sidebar if needed
        4. **Click "Generate Subtitles"**
        5. **Download** your SRT file when processing is complete
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### Script Format Requirements")
        st.info("""
        Your script should follow this format:
        
        CHARACTER: Dialog text.
        
        ANOTHER CHARACTER: More dialog text.
        
        The app will extract dialog lines and match them with the video's audio.
        """)
        
        # Example script button (collapsible)
        with st.expander("View Example Script"):
            st.code("""
DOCTOR: People don't understand time. It's not what you think it is.

SALLY: Then what is it?

DOCTOR: Complicated.

SALLY: Tell me.

DOCTOR: Very complicated.

SALLY: I'm clever and I'm listening. And don't patronise me because people have died, and I'm not happy. Tell me.
            """)
    
    # Progress display and results area (full width)
    progress_placeholder = st.empty()
    results_container = st.container()
    
    # Process files when button is clicked
    if process_button:
        # Setup progress bar and status
        progress_bar = progress_placeholder.progress(0)
        status_container = progress_placeholder.empty()
        
        def update_progress(message, progress_value, error=False, intermediate=False):
            """Update progress bar and status message."""
            if not intermediate:
                progress_bar.progress(progress_value)
            
            if error:
                status_container.error(message)
            else:
                status_container.info(message)
        
        # Process files
        result = process_files(
            video_file, 
            script_content, 
            include_character=include_character,
            model_size=model_size,
            similarity_threshold=similarity_threshold,
            max_words=max_words,
            progress_callback=update_progress
        )
        
        # Display results
        if result:
            with results_container:
                st.markdown('<p class="sub-header">✅ Processing Complete!</p>', unsafe_allow_html=True)
                
                tabs = st.tabs(["Results", "Preview", "Statistics"])
                
                with tabs[0]:
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown("### Your subtitle file is ready!")
                    download_link = get_download_link(
                        result["srt_content"], 
                        "subtitles.srt", 
                        "📥 Download SRT File"
                    )
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Raw SRT preview
                    with st.expander("View SRT Content"):
                        st.text(result["srt_content"])
                
                with tabs[1]:
                    # Show table of first 10 subtitles
                    st.subheader("Subtitle Preview")
                    preview_data = []
                    for i, segment in enumerate(result["aligned_segments"][:10]):
                        preview_data.append({
                            "Index": i + 1,
                            "Start Time": f"{int(segment['start'] // 60):02d}:{int(segment['start'] % 60):02d}.{int((segment['start'] % 1) * 1000):03d}",
                            "End Time": f"{int(segment['end'] // 60):02d}:{int(segment['end'] % 60):02d}.{int((segment['end'] % 1) * 1000):03d}",
                            "Character": segment.get('character', 'N/A'),
                            "Text": segment['text'],
                            "Match Score": f"{segment.get('match_score', 0) * 100:.1f}%"
                        })
                    
                    st.dataframe(preview_data, use_container_width=True)
                    st.caption("Showing first 10 subtitles. Download the full SRT file for complete results.")
                
                with tabs[2]:
                    stats = result["stats"]
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    
                    with col_a:
                        st.metric("Processing Time", f"{stats['processing_time']:.1f}s")
                    
                    with col_b:
                        st.metric("Script Lines", stats['dialog_lines'])
                    
                    with col_c:
                        st.metric("Speech Segments", stats['speech_segments'])
                    
                    with col_d:
                        st.metric("Total Subtitles", stats['subtitle_segments'])
                    
                    # Match score distribution chart
                    match_scores = [segment.get('match_score', 0) for segment in result["aligned_segments"] if 'match_score' in segment]
                    if match_scores:
                        score_df = pd.DataFrame({
                            'Match Score': [score * 100 for score in match_scores]
                        })
                        
                        fig = px.histogram(
                            score_df, 
                            x='Match Score',
                            title='Distribution of Match Scores (%)',
                            labels={'Match Score': 'Similarity Score (%)'},
                            color_discrete_sequence=['#1E88E5'],
                            nbins=20
                        )
                        fig.update_layout(
                            xaxis_range=[0, 100],
                            xaxis_ticksuffix='%'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
            # Clear progress display
        progress_placeholder.empty()

if __name__ == "__main__":
    main() 