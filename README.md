Real-Time Speech-to-Speech Machine Translation System

Project Overview

This project is a real-time Speech-to-Speech Machine Translation (S2ST) system . 
The main goal of the project is to take spoken input from a user through the microphone, process the audio, 
identify the language, convert speech into text, translate that text into a target language,
generate synthesized speech for the translated output, and then play the translated audio back to the user.


Implemented pipeline

Microphone Input → Audio Streaming → Noise Suppression → VAD → LID → ASR → Translation → TTS → Audio Output

This system is designed as a working MVP (Minimum Viable Product) for real-time multilingual speech translation.


Objective

The objective of this project is to build a modular real-time speech-to-speech translation system that can:

- capture live audio from a microphone
- process speech in small chunks
- reduce noise
- detect whether the user is speaking or silent
- identify the source language
- transcribe speech into text
- translate the recognized text into a target language
- convert translated text back into speech
- play the translated speech output

The project aims to demonstrate an end-to-end real-time translation workflow that is practical, understandable,
and extendable.


Technologies Used

1. Python
Python was used as the main programming language because it is simple, readable,
and has strong support for speech processing, machine learning, and real-time audio libraries.

2. sounddevice
Used for real-time microphone capture.

Why it was used:
- captures live microphone audio directly
- supports chunk-based audio streaming
- easy to integrate with Python

How it was used:
- the microphone input is captured continuously
- audio is received in 30 ms chunks
- each chunk is pushed into a queue for further processing

3. noisereduce
Used for basic noise suppression.

Why it was used:
- improves audio clarity before speech recognition
- reduces environmental noise
- simple and quick to integrate for an MVP

How it was used:
- after a speech segment is collected, noise reduction is applied before sending audio to ASR

4. webrtcvad
Used for Voice Activity Detection (VAD).

Why it was used:
- detects whether a chunk contains speech or silence
- prevents unnecessary processing of silent audio
- improves efficiency in real-time systems

How it was used:
- every 30 ms audio frame is passed to WebRTC VAD
- if speech is detected, the chunk is stored
- if silence continues for enough frames, the segment is ended and processed

5. faster-whisper
Used for:
- Automatic Speech Recognition (ASR)
- Language Identification (LID)

Why it was used:
- faster than regular Whisper in many cases
- can run locally
- provides language detection and transcription together
- gives timestamps for recognized segments

How it was used:
- speech segments are saved as WAV files
- faster-whisper transcribes the speech
- the model also returns the detected language and confidence score
- timestamps are extracted for alignment

6. deep-translator
Used for text translation.

Why it was used:
- simple API
- easy to use for multilingual translation
- good enough for a hackathon MVP

How it was used:
- the transcribed text is passed to the translator
- source language is automatically detected
- output is translated into the selected target language

7. edge-tts
Used for Text-to-Speech (TTS).

Why it was used:
- supports natural neural voices
- supports multiple languages
- easy to integrate into Python
- suitable for quick speech generation

How it was used:
- translated text is converted into speech
- the voice is selected based on the target language
- the generated MP3 file is played as output

8. Streamlit
Used for a simple demo UI.

Why it was used:
- easy to build a lightweight interface quickly
- useful for showing logs and target language selection
- improves hackathon demo presentation

How it was used:
- a simple UI was created
- the UI allows target language selection
- the UI reads logs from the backend
- the UI updates target language through a config file

9. JSON config file
Used to connect frontend and backend.

Why it was used:
- simple way to change target language dynamically
- avoids hardcoding language every time
- no backend restart required in the improved version

How it was used:
- `config.json` stores the selected target language
- the Streamlit UI updates this file
- the backend reads this file before translation



## Project Structure

speech_translation_project/
│
├── app.py
├── demo_ui.py
├── config.json
├── requirements.txt
├── translation_log.txt
├── README.md
├── temp/
└── venv/


Completion Status (Based on Hackathon Requirements)

Completed Features

Audio & Input
Audio Processing
Speech Detection
Language Processing
Speech Recognition
Translation
Speech Synthesis
Output
- Translated speech playback  
- Real-time response after each speech segment  

 System Features
- End-to-end working pipeline  
- Modular code structure (functions for each stage)  
- Logging system (translation_log.txt)  
- Basic error handling  
- Simple UI using Streamlit for demo  


Partially Completed Features

Audio Processing
- Only basic noise suppression is implemented  
- Advanced speech enhancement (RNNoise, deep models) not used  

Language Processing
- Handles multilingual input, but:
  - No code-switching detection (mixed languages in one sentence)  

Translation
- Works correctly at sentence level  
- Does not maintain context across multiple sentences  

Output
- Segment-based output (not continuous streaming speech)  
- Small delay between speaking and output  



Not Completed Yet

Advanced Audio Processing
- Deep-learning-based noise suppression (RNNoise, LogMMSE, etc.)  
- Real-time frame-level denoising  

Advanced Language Handling
- Code-switching detection  
- Multi-language mixing in the same sentence  

Context-Aware Translation
- No memory across sentences  
- No context-aware models like mBART or mT5  

True Real-Time Streaming
- No token-by-token or word-by-word streaming  
- System processes full speech segments instead  

Smooth Streaming Output
- Audio output is not continuous (plays per segment)  

Scalability & Deployment
- Not deployed on cloud  
- No API-based architecture  
- Not optimized for multiple users  

Advanced UI
- No live waveform display  
- No real-time transcript panel  
- No detailed pipeline visualization  



## Overall Status

- Core pipeline:  Fully working  
- Real-time interaction:  Achieved (segment-level)  
- Accuracy & performance: Moderate (depends on mic & environment)  
- Production readiness: Not yet (currently MVP)

