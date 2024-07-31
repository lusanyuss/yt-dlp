import logging
import os
import time

from faster_whisper import WhisperModel  # 假设这是一个已安装的库
from moviepy.config import change_settings

from yuliu.utils import print_yellow, get_path_without_suffix

# 设置环境变量
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 指定 ImageMagick 的路径
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


def transcribe_audio_to_srt(audio_path, language='zh', model_size="large-v3", device="cuda", compute_type="float16", sub_directory=""):
    base, ext = os.path.splitext(audio_path)
    base_name = get_path_without_suffix(base)
    srt_path = f"{base_name}_{language}.srt"
    temp_srt_path = f"{base_name}_{language}_temp.srt"

    if os.path.exists(temp_srt_path):
        os.remove(temp_srt_path)
    if os.path.exists(srt_path):
        print_yellow(f"字幕文件已存在: {srt_path}")
        return srt_path

    print("加载模型...")
    logging.basicConfig()
    logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

    try:
        start_time1 = time.time()
        model = WhisperModel(model_size_or_path=model_size, device=device, compute_type=compute_type)
        segments, info = model.transcribe(
            audio=audio_path,
            language="zh",  # 假设对话是中文的
            task="transcribe",
            beam_size=5,
            best_of=1,  # 提高处理速度，因为背景噪音较少
            patience=0.5,  # 更快的响应时间
            length_penalty=0.8,  # 稍微偏向更短的输出
            repetition_penalty=1.2,  # 避免重复
            no_repeat_ngram_size=3,  # 防止3个词的重复
            temperature=0.5,  # 控制输出的随机性，保持较高的确定性
            compression_ratio_threshold=1.5,  # 较低的压缩比，以保持对话的完整性
            no_speech_threshold=0.4,  # 适中的无语音阈值
            vad_filter=True,  # 启用VAD
            vad_parameters={"min_silence_duration_ms": 200},  # 200ms的静音识别，适合快速对话
            word_timestamps=True,  # 为每个单词生成时间戳
            suppress_blank=True,  # 抑制空白段落
            without_timestamps=False  # 输出带时间戳的转录
        )
        print(f"开始转录音频: {time.time() - start_time1:.2f} 秒")
        print(f"将结果写入临时SRT文件: {temp_srt_path}")

        start_time2 = time.time()
        with open(temp_srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(segments, start=1):
                start = segment.start
                end = segment.end
                text = segment.text

                start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start * 1000) % 1000):03}"
                end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end * 1000) % 1000):03}"

                srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        print(f"将结果写入临时SRT文件: {time.time() - start_time2:.2f} 秒")
        # 去掉大模型添加的前尾30秒加密信息
        # temp_srt_path = process_srt(temp_srt_path)
        os.replace(temp_srt_path, srt_path)
        print(f"字幕已保存到 {srt_path}")
    except Exception as e:
        if os.path.exists(temp_srt_path):
            os.remove(temp_srt_path)
        print(f"发生异常: {str(e)}")
        raise e
    return srt_path


if __name__ == '__main__':
    # Usage
    audio_file_path = "release_video/aa归来之非凡人生test/aa归来之非凡人生test_nobgm_audio.wav"
    transcribe_audio_to_srt(audio_file_path)
