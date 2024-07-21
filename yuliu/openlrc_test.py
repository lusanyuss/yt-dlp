import whisperx
import re

device = "cpu"
audio_file = "C:/yuliu/workspace/yt-dlp/yuliu/res/1.wav"
batch_size = 16
compute_type = "float32"

# 加载 WhisperX 模型
model = whisperx.load_model("large-v2", device, compute_type=compute_type)
audio = whisperx.load_audio(audio_file)
result = model.transcribe(audio, batch_size=batch_size)

# 对 WhisperX 输出进行对齐
model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

# 生成 LRC 文件并保存到 ./yuliu/res/
segments = result["segments"]
output_file = "C:/yuliu/workspace/yt-dlp/yuliu/res/1_1min.lrc"


def split_sentences(text):
    sentence_endings = re.compile(r'([。！？])')
    parts = sentence_endings.split(text)
    sentences = [''.join(parts[i:i + 2]) for i in range(0, len(parts) - 1, 2)]
    if len(parts) % 2 != 0:
        sentences.append(parts[-1])
    return sentences


# 写入 LRC 文件
with open(output_file, "w", encoding="utf-8") as f:
    for segment in segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text']

        # 使用正则表达式进行分句
        sentences = split_sentences(text)

        num_sentences = len(sentences)
        duration_per_sentence = (end_time - start_time) / num_sentences

        for i, sentence in enumerate(sentences):
            sentence = sentence.rstrip('。！？')  # 去掉句末标点符号
            sentence_start_time = start_time + i * duration_per_sentence
            minutes, seconds = divmod(sentence_start_time, 60)
            milliseconds = (sentence_start_time - int(sentence_start_time)) * 1000
            timestamp = f"[{int(minutes):02}:{int(seconds):02}.{int(milliseconds):03}]"
            f.write(f"{timestamp}{sentence}\n")
