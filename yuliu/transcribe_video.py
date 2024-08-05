import logging
import os
import time

from faster_whisper import WhisperModel  # 假设这是一个已安装的库
from moviepy.config import change_settings

from yuliu.utils import extract_audio_only
from yuliu.utils import print_yellow, get_path_without_suffix, print_red

# 设置环境变量
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 指定 ImageMagick 的路径
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


def transcribe_audio_to_srt(video_nobgm, language='zh', model_size="large-v2", device="cuda", compute_type="float16"):
    base, ext = os.path.splitext(video_nobgm)
    base_name = get_path_without_suffix(base)
    srt_path = f"{base_name}_{language}.srt"
    temp_srt_path = f"{base_name}_{language}_temp.srt"

    if os.path.exists(temp_srt_path):
        os.remove(temp_srt_path)
    if os.path.exists(srt_path):
        print_yellow(f"字幕文件已存在: {srt_path}")
        return srt_path

    audio_path = extract_audio_only(video_nobgm)
    print("加载模型...")
    logging.basicConfig()
    logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

    try:
        start_time1 = time.time()
        model = WhisperModel(model_size_or_path=model_size, device=device, compute_type=compute_type)
        initial_prompt_text = "以下是普通话的句子。"
        segments, info = model.transcribe(
            audio=audio_path,
            language="zh",  # 假设对话是中文
            task="transcribe",
            beam_size=10,  # 使用较大的beam size以提高识别准确性
            best_of=3,  # 从多个候选中选择最佳输出，提高质量
            patience=0.8,  # 增加等待概率改善的时间，以获得更准确的结果
            length_penalty=1.0,  # 保持标准长度，避免对输出进行惩罚或奖励
            repetition_penalty=1.1,  # 轻微增加重复惩罚，避免内容的重复
            no_repeat_ngram_size=4,  # 防止近距离的4个词的重复，提高内容的多样性
            temperature=[0.0],  # 保持输出的一致性和确定性
            compression_ratio_threshold=2.0,  # 适当的压缩比，保留更多细节
            log_prob_threshold=-0.5,  # 设置一个较高的日志概率阈值以确保内容质量
            no_speech_threshold=0.3,  # 较低的无语音阈值，因为背景已清除
            condition_on_previous_text=True,  # 使用上下文信息提高连贯性
            word_timestamps=True,  # 每个单词生成时间戳，提高字幕的时间准确性
            vad_filter=True,  # 启用VAD来检测有效语音活动
            vad_parameters={"min_silence_duration_ms": 250},  # 150毫秒的最小静音时长，平衡对话自然停顿和快速响应
            without_timestamps=False,  # 生成带时间戳的输出，对SRT文件必须
            suppress_blank=True,  # 抑制无语音的输出，减少字幕中的空白
            initial_prompt=initial_prompt_text
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
        print_red(f"发生异常: {str(e)}")
        raise e
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    return srt_path


if __name__ == '__main__':
    # Usage
    audio_file_path = "release_video/aa下山后我被四个绝色师姐包围了/aa归来之非凡人生test_nobgm_audio.wav"
    transcribe_audio_to_srt(audio_file_path)
