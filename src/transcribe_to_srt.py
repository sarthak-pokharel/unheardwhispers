from pydub import AudioSegment
import whisper
import pysrt
import os
import re
import nltk
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from tqdm import tqdm
import time
import sys
import subprocess

# Download NLTK resources (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Ensure FFmpeg can be found if it's in a local directory
def initialize_local_ffmpeg():
    """Ensure FFmpeg binaries in project directory are properly detected."""
    try:
        # Get script directory (or current working directory)
        if getattr(sys, 'frozen', False):
            # Running as executable
            script_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Check for local FFmpeg in the project's tools directory
        ffmpeg_path = os.path.join(script_dir, "tools", "ffmpeg", "bin")
        
        if os.path.exists(ffmpeg_path):
            # Add to PATH if not already there
            if ffmpeg_path not in os.environ['PATH']:
                os.environ['PATH'] = ffmpeg_path + os.pathsep + os.environ['PATH']
                print(f"Using local FFmpeg from: {ffmpeg_path}")
        
        # Verify FFmpeg is available
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("WARNING: FFmpeg not found in PATH. Audio processing may fail.")
            return False
            
    except Exception as e:
        print(f"Error initializing local FFmpeg: {e}")
        return False

# Initialize local FFmpeg on module import
initialize_local_ffmpeg()

def extract_audio_from_video(video_file_path, audio_file_path):
    """Extract audio from video file."""
    try:
        video = AudioSegment.from_file(video_file_path)
        video.export(audio_file_path, format="mp3")
        return True
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False

def convert_audio_to_wav(audio_file_path, temp_wav_path):
    """Convert audio to WAV format for Whisper processing."""
    try:
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(temp_wav_path, format="wav")
        return True
    except Exception as e:
        print(f"Error converting audio to WAV: {e}")
        return False

def extract_dialog_from_script(script_file_path):
    """Extract all dialog lines from the script file, preserving exact text."""
    try:
        with open(script_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        dialog_lines = []
        
        # Improved regex pattern for dialog extraction
        dialog_pattern = re.compile(r'([A-Z]+(?:\s[A-Z]+)*)(?:\s\([^)]*\))?:\s*(.*?)(?=\n\n|\n[A-Z]+(?:\s[A-Z]+)*(?:\s\([^)]*\))?:|\Z)', re.DOTALL)
        
        matches = dialog_pattern.findall(content)
        for character, text in matches:
            # Clean up the text (remove newlines but preserve exact words)
            clean_text = re.sub(r'\n\s*', ' ', text.strip())
            if clean_text:
                dialog_lines.append({
                    'character': character.strip(),
                    'text': clean_text
                })
        
        return dialog_lines
    except Exception as e:
        print(f"Error extracting dialog from script: {e}")
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

def break_dialog_into_chunks(dialog_lines, max_words=10):
    """Break dialog lines into smaller chunks for more precise matching."""
    chunks = []
    
    for line in dialog_lines:
        character = line['character']
        text = line['text']
        
        # Use NLTK to split into sentences
        sentences = nltk.sent_tokenize(text)
        
        for sentence in sentences:
            chunks.extend(chunk_sentence(sentence, character, max_words))
    
    return chunks

def get_whisper_segments_with_text(temp_wav_path, model):
    """Get timing and transcribed text from Whisper for matching purposes."""
    try:
        print("Transcribing audio with Whisper...")
        start_time = time.time()
        result = model.transcribe(temp_wav_path, task="transcribe")
        elapsed = time.time() - start_time
        print(f"Transcription completed in {elapsed:.2f} seconds")
        
        segments = []
        for segment in result['segments']:
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'transcribed_text': segment['text'].strip()
            })
            
        return segments
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return []

def whisper_segments_to_subtitles(whisper_segments):
    """Convert Whisper segments directly to subtitle segments without script matching."""
    subtitle_segments = []
    
    for segment in whisper_segments:
        subtitle_segments.append({
            'start': segment['start'],
            'end': segment['end'],
            'text': segment['transcribed_text'],
            'character': None
        })
    
    return subtitle_segments

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

def align_script_chunks_with_segments(script_chunks, whisper_segments, threshold=0.3, max_workers=4):
    """Align script chunks with Whisper segments by finding best matches."""
    aligned_segments = []
    used_chunks = set()
    
    # Prepare arguments for parallel processing
    args_list = [(segment, script_chunks, used_chunks, threshold) for segment in whisper_segments]
    
    # Use ThreadPoolExecutor for parallel processing
    print(f"Aligning {len(whisper_segments)} segments with {len(script_chunks)} script chunks...")
    
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
    
    return aligned_segments

def generate_srt_from_segments(segments, srt_file_path, include_character=True):
    """Generate SRT file from aligned segments."""
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
    
    try:
        srt_subs.save(srt_file_path, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error saving SRT file: {e}")
        return False

def transcribe_audio_to_srt(audio_file_path, srt_file_path, script_file_path=None, include_character=True, model_size="base"):
    """Main function to transcribe audio and align with script text (if provided)."""
    # Setup
    temp_wav_path = "temp.wav"
    start_time = time.time()
    
    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)
    
    # Convert audio
    print("Converting audio to WAV format...")
    if not convert_audio_to_wav(audio_file_path, temp_wav_path):
        return False
    
    # Get timing segments and transcribed text from Whisper
    whisper_segments = get_whisper_segments_with_text(temp_wav_path, model)
    if not whisper_segments:
        print("No speech segments detected.")
        return False
    
    # Check if script file is provided
    if script_file_path:
        # Use script file content for subtitles
        print("Extracting dialog from script file...")
        dialog_lines = extract_dialog_from_script(script_file_path)
        if not dialog_lines:
            print("No dialog found in script file. Falling back to Whisper transcription.")
            aligned_segments = whisper_segments_to_subtitles(whisper_segments)
        else:
            # Break dialog lines into smaller chunks
            print("Breaking dialog into smaller chunks...")
            script_chunks = break_dialog_into_chunks(dialog_lines)
            print(f"Created {len(script_chunks)} script chunks from {len(dialog_lines)} dialog lines")
            
            # Align script chunks with Whisper segments
            aligned_segments = align_script_chunks_with_segments(script_chunks, whisper_segments)
            print(f"Created {len(aligned_segments)} aligned segments")
    else:
        # No script file provided, use Whisper transcription directly
        print("No script file provided. Using Whisper transcription directly.")
        aligned_segments = whisper_segments_to_subtitles(whisper_segments)
        print(f"Created {len(aligned_segments)} subtitle segments from Whisper transcription")
    
    # Generate SRT file
    print("Generating SRT file...")
    if not generate_srt_from_segments(aligned_segments, srt_file_path, include_character):
        return False
    
    # Cleanup
    if os.path.exists(temp_wav_path):
        os.remove(temp_wav_path)
    
    elapsed = time.time() - start_time
    print(f"Total processing time: {elapsed:.2f} seconds")
    return True
