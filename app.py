import os
import re
import json
import wave
import uuid
import time
import queue
import asyncio
import threading

import numpy as np
import sounddevice as sd
import noisereduce as nr
import webrtcvad

from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
import edge_tts


# -----------------------------
# Basic settings
# -----------------------------
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

VAD_MODE = 1
SILENCE_FRAMES = 12
MIN_SPEECH_FRAMES = 5

TEMP_FOLDER = "temp"
LOG_FILE = "translation_log.txt"
CONFIG_FILE = "config.json"

MIN_AUDIO_SECONDS = 0.45
MIN_ENERGY = 0.003
MIN_LANGUAGE_CONFIDENCE = 0.35
PLAYBACK_WAIT = 2.5

os.makedirs(TEMP_FOLDER, exist_ok=True)


# -----------------------------
# Queues and flags
# -----------------------------
audio_queue = queue.Queue()
segment_queue = queue.Queue()

is_playing = False
is_processing = False
last_play_time = 0
lock = threading.Lock()


# -----------------------------
# Load target language from config
# -----------------------------
def get_target_language():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("target_language", "te")
        except Exception:
            return "te"
    return "te"


# -----------------------------
# Load models
# -----------------------------
print("Loading ASR model...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
vad = webrtcvad.Vad(VAD_MODE)

print(f"Current target language: {get_target_language()}")
print("System ready. Speak into the microphone...")


# -----------------------------
# Mic callback
# -----------------------------
def mic_callback(indata, frames, time_info, status):
    if status:
        print("\nMic status:", status)
    audio_queue.put(indata.copy())


# -----------------------------
# Small helper functions
# -----------------------------
def reduce_noise(audio):
    if len(audio) < SAMPLE_RATE // 2:
        return audio

    try:
        cleaned = nr.reduce_noise(y=audio, sr=SAMPLE_RATE)
        return cleaned.astype(np.float32)
    except Exception as e:
        print("\nNoise reduction error:", e)
        return audio


def save_wav(audio, path):
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())


def get_rms(audio):
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio))))


def valid_text(text):
    if not text:
        return False

    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    if re.fullmatch(r"[^\w]+", text):
        return False

    if re.fullmatch(r"(\.\s*)+", text):
        return False

    if not re.search(r"[A-Za-z0-9\u0C00-\u0C7F]", text):
        return False

    if len(text) <= 1:
        return False

    return True


def write_log(source_lang, original_text, translated_text, target_lang):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Detected Language: {source_lang}\n")
            f.write(f"Recognized Text: {original_text}\n")
            f.write(f"Translated Text ({target_lang}): {translated_text}\n")
            f.write("-" * 50 + "\n")
    except Exception as e:
        print("\nLog error:", e)


def system_busy():
    with lock:
        if is_playing or is_processing:
            return True
        if time.time() - last_play_time < 0.8:
            return True
    return False


# -----------------------------
# ASR + LID
# -----------------------------
def transcribe_audio(wav_path):
    segments, info = whisper_model.transcribe(
        wav_path,
        beam_size=1,
        vad_filter=False,
        language=None
    )

    parts = []
    timestamps = []

    for seg in segments:
        seg_text = seg.text.strip()
        if seg_text:
            parts.append(seg_text)
            timestamps.append((seg.start, seg.end, seg_text))

    full_text = " ".join(parts).strip()
    detected_lang = info.language if hasattr(info, "language") else "unknown"
    confidence = getattr(info, "language_probability", None)

    return full_text, detected_lang, confidence, timestamps


# -----------------------------
# Translation
# -----------------------------
def translate_text(text, target_lang):
    if not text.strip():
        return ""

    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as e:
        print("\nTranslation error:", e)
        return ""


# -----------------------------
# TTS
# -----------------------------
async def make_speech_async(text, target_lang, output_file):
    voices = {
        "en": "en-US-AriaNeural",
        "hi": "hi-IN-SwaraNeural",
        "te": "te-IN-ShrutiNeural",
        "ta": "ta-IN-PallaviNeural",
        "fr": "fr-FR-DeniseNeural",
        "es": "es-ES-ElviraNeural",
    }

    voice = voices.get(target_lang, "en-US-AriaNeural")
    tts = edge_tts.Communicate(text=text, voice=voice)
    await tts.save(output_file)


def make_speech(text, target_lang):
    output_file = os.path.join(TEMP_FOLDER, f"{uuid.uuid4().hex}.mp3")

    try:
        asyncio.run(make_speech_async(text, target_lang, output_file))
        return output_file
    except Exception as e:
        print("\nTTS error:", e)
        return None


def play_audio(file_path):
    global is_playing, last_play_time

    try:
        with lock:
            is_playing = True
            last_play_time = time.time()

        print(f"[TTS] Playing: {file_path}")
        os.startfile(os.path.abspath(file_path))
        time.sleep(PLAYBACK_WAIT)

    except Exception as e:
        print("\nPlayback error:", e)

    finally:
        with lock:
            is_playing = False
            last_play_time = time.time()


# -----------------------------
# Process one speech segment
# -----------------------------
def process_segment(audio):
    target_lang = get_target_language()

    duration = len(audio) / SAMPLE_RATE
    energy = get_rms(audio)

    if duration < MIN_AUDIO_SECONDS:
        print("\nSkipped: audio too short.")
        return

    if energy < MIN_ENERGY:
        print(f"\nSkipped: low energy. RMS={energy:.5f}")
        return

    print(f"\n\nProcessing speech... [Target={target_lang}]")

    cleaned_audio = reduce_noise(audio)

    wav_path = os.path.join(TEMP_FOLDER, f"{uuid.uuid4().hex}.wav")
    save_wav(cleaned_audio, wav_path)

    text, source_lang, lid_conf, timestamps = transcribe_audio(wav_path)

    if not valid_text(text):
        print("No meaningful transcription found.")
        return

    if lid_conf is not None and lid_conf < MIN_LANGUAGE_CONFIDENCE:
        print(f"Skipped: low language confidence ({lid_conf:.3f})")
        return

    print(f"[LID] Language: {source_lang} | Confidence: {lid_conf}")
    print(f"[ASR] {text}")

    translated = translate_text(text, target_lang)
    if not translated or not translated.strip():
        print("Translation failed.")
        return

    print(f"[Translated -> {target_lang}] {translated}")

    write_log(source_lang, text, translated, target_lang)

    mp3_file = make_speech(translated, target_lang)
    if mp3_file:
        play_audio(mp3_file)

    print("[Timestamps]")
    for start, end, seg_text in timestamps:
        print(f"  {start:.2f}s - {end:.2f}s : {seg_text}")


# -----------------------------
# Worker thread
# -----------------------------
def worker():
    global is_processing

    while True:
        audio = segment_queue.get()

        with lock:
            is_processing = True

        try:
            process_segment(audio)
        except Exception as e:
            print("\nWorker error:", e)
        finally:
            with lock:
                is_processing = False
            segment_queue.task_done()


# -----------------------------
# Main streaming loop
# -----------------------------
def run():
    speech_frames = []
    speech_count = 0
    silence_count = 0

    threading.Thread(target=worker, daemon=True).start()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=FRAME_SIZE,
        callback=mic_callback,
    ):
        while True:
            chunk = audio_queue.get()

            if system_busy():
                continue

            audio_chunk = chunk.flatten()
            frame_bytes = audio_chunk.tobytes()

            try:
                speaking = vad.is_speech(frame_bytes, SAMPLE_RATE)
            except Exception:
                continue

            if speaking:
                speech_frames.append(audio_chunk.copy())
                speech_count += 1
                silence_count = 0
                print(".", end="", flush=True)
            else:
                if speech_frames:
                    speech_frames.append(audio_chunk.copy())
                    silence_count += 1
                    print("_", end="", flush=True)

            if speech_frames and silence_count >= SILENCE_FRAMES:
                if speech_count >= MIN_SPEECH_FRAMES:
                    full_audio = np.concatenate(speech_frames).astype(np.float32) / 32768.0
                    segment_queue.put(full_audio)
                else:
                    print("\nIgnored: speech was too short.")

                speech_frames = []
                speech_count = 0
                silence_count = 0


# -----------------------------
# Start app
# -----------------------------
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")