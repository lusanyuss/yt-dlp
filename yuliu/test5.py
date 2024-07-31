import os

import whisper


def format_time(ms):
    """ Helper function to convert milliseconds to SRT time format """
    sec, ms = divmod(ms, 1000)
    min, sec = divmod(sec, 60)
    hr, min = divmod(min, 60)
    return f'{int(hr):02}:{int(min):02}:{int(sec):02},{int(ms):03}'


def generate_srt(segments):
    """ Generate SRT content from segments """
    srt_content = ""
    for i, segment in enumerate(segments):
        start = format_time(segment['start'])
        end = format_time(segment['end'])
        text = segment['text']
        srt_content += f"{i + 1}\n{start} --> {end}\n{text}\n\n"
    return srt_content


def transcribe_to_srt(audio_path, model_type="large-v2", language="zh"):
    # Load the model
    model = whisper.load_model(model_type)

    # Transcribe the audio
    result = model.transcribe(audio_path, language=language)

    # Generate SRT file content
    srt_content = generate_srt(result['segments'])

    # Write to SRT file
    srt_filename = os.path.splitext(audio_path)[0] + ".srt"  # Creates a new filename with .srt extension
    with open(srt_filename, "w") as f:
        f.write(srt_content)

if __name__ == '__main__':
    # Usage
    audio_file_path = "release_video/aa归来之非凡人生test/aa归来之非凡人生test_nobgm_audio.wav"
    transcribe_to_srt(audio_file_path)
