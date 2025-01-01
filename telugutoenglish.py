import whisper
import azure.cognitiveservices.speech as speechsdk
import gradio as gr
from dotenv import load_dotenv
import os
from datetime import datetime  # For timestamp generation

# Load environment variables from .env file
load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SERVICE_REGION = os.getenv("AZURE_SERVICE_REGION")

def transcribe_and_translate_with_whisper(file_path, model_type="large"):
    """
    Transcribe Telugu audio to English text using Whisper.

    Args:
        file_path (str): Path to the audio file.
        model_type (str): Whisper model type. Options: "tiny", "base", "small", "medium", "large".

    Returns:
        str: Translated English text.
    """
    print(f"Loading Whisper model ({model_type})...")
    model = whisper.load_model(model_type)

    print("Transcribing and translating audio...")
    result = model.transcribe(file_path, task="translate", language="te")

    # Extract the translated English text
    translated_text = result.get("text", "")
    print(f"Translated English Text: {translated_text}")
    return translated_text

def synthesize_speech_with_azure(english_text, output_file):
    """
    Convert translated English text into speech using Azure Speech Service.

    Args:
        english_text (str): The English text to be converted to speech.
        output_file (str): Path to save the output audio file.
    """
    print("Synthesizing speech with Azure...")
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SERVICE_REGION)
    audio_output = speechsdk.audio.AudioOutputConfig(filename=output_file)

    # Create a speech synthesizer with the Azure config
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

    # Convert text to speech
    result = synthesizer.speak_text_async(english_text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Speech synthesis completed. Audio saved to {output_file}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")

def process_audio(file_path, model_type):
    """
    Process the uploaded Telugu audio file, transcribe it to English, and synthesize speech.

    Args:
        file_path (str): Path to the uploaded Telugu audio file.
        model_type (str): Whisper model type (e.g., "tiny", "base", "small", "medium", "large").

    Returns:
        str, str: Translated English text and path to synthesized audio file.
    """
    # Step 1: Transcribe and translate Telugu audio to English text using Whisper
    print(f"Processing file: {file_path}")
    translated_text = transcribe_and_translate_with_whisper(file_path, model_type=model_type)

    # Step 2: Generate a unique filename for the synthesized audio file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Generate a timestamp
    output_audio_file = f"translated_audio_{timestamp}.wav"

    # Step 3: If translation is successful, convert the English text to speech using Azure
    if translated_text:
        synthesize_speech_with_azure(translated_text, output_audio_file)

    # Return translated text and synthesized audio file path
    return translated_text, output_audio_file

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## Telugu to English Audio Translation for Audio Files")

    audio_input = gr.Audio(label="Upload Audio File", type="filepath")
    model_type = gr.Dropdown(choices=["tiny", "base", "small", "medium", "large"], value="large", label="Whisper Model")
    translate_button = gr.Button("Process Audio")
    translated_text = gr.Textbox(label="Translated English Text", interactive=False)
    output_audio = gr.Audio(label="Synthesized English Speech", type="filepath", interactive=False)

    translate_button.click(
        process_audio,
        inputs=[audio_input, model_type],
        outputs=[translated_text, output_audio],
    )

demo.launch(share=True)
