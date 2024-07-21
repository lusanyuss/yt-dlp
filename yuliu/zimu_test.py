import os
import textwrap

import srt
from faster_whisper import WhisperModel
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from translate import Translator

# 设置环境变量
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 指定 ImageMagick 的路径
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

# 设置字体路径
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"  # 请确保该路径正确


def transcribe_audio_to_srt(audio_path, output_srt_path, model_size="large-v2", device="cpu", compute_type="int8"):
    if os.path.exists(output_srt_path):
        print(f"字幕文件已存在: {output_srt_path}")
        return output_srt_path

    print("加载模型...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    print("开始转录音频...")
    segments, info = model.transcribe(audio_path, beam_size=5)

    print(f"将结果写入SRT文件: {output_srt_path}")
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments, start=1):
            start = segment.start
            end = segment.end
            text = segment.text

            start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start * 1000) % 1000):03}"
            end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end * 1000) % 1000):03}"

            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

    print(f"字幕已保存到 {output_srt_path}")
    return output_srt_path


def translate_srt_to_english(srt_path, translated_srt_path):
    if os.path.exists(translated_srt_path):
        print(f"翻译后的字幕文件已存在: {translated_srt_path}")
        return translated_srt_path

    translator = Translator(to_lang="en")
    with open(srt_path, 'r', encoding='utf-8') as file:
        subtitles = list(srt.parse(file.read()))

    translated_subtitles = []
    for subtitle in subtitles:
        translated_text = translator.translate(subtitle.content)
        print(f"翻译前: {subtitle.content}")
        print(f"翻译后: {translated_text}")
        translated_subtitles.append(srt.Subtitle(index=subtitle.index, start=subtitle.start, end=subtitle.end, content=translated_text))

    with open(translated_srt_path, 'w', encoding='utf-8') as file:
        file.write(srt.compose(translated_subtitles))

    print(f"翻译后的字幕已保存到 {translated_srt_path}")
    return translated_srt_path


def add_subtitles_to_video(video_path, srt_path, output_path, subtitle_width_ratio=0.90, subtitle_y_position=280):
    print(f"读取视频文件: {video_path}")
    video = VideoFileClip(video_path)
    video_width, video_height = video.size
    print(f"视频尺寸: {video_width}x{video_height}")

    translated_srt_path = srt_path.replace('.srt', '_translated.srt')
    srt_path = translate_srt_to_english(srt_path, translated_srt_path)

    print(f"读取字幕文件: {srt_path}")
    with open(srt_path, 'r', encoding='utf-8') as file:
        subtitles = list(srt.parse(file.read()))

    clips = []

    subtitle_width = video_width * subtitle_width_ratio
    max_chars_per_line = int(subtitle_width // 20)

    for subtitle in subtitles:
        start_time = subtitle.start.total_seconds()
        end_time = subtitle.end.total_seconds()
        text = subtitle.content

        wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))

        try:
            txt_clip = (TextClip(wrapped_text, fontsize=36, color='white', font=FONT_PATH, size=(subtitle_width, None))
                        .on_color(color=(0, 0, 0), col_opacity=0.6)
                        .set_position(('center', video_height - subtitle_y_position))
                        .set_start(start_time)
                        .set_duration(end_time - start_time))

            print(f"创建字幕: '{wrapped_text}' 从 {start_time} 到 {end_time}, 位置: bottom")
            print(f"字幕文本剪辑: {txt_clip}")

            clips.append(txt_clip)
        except Exception as e:
            print(f"创建字幕时出错: {e}")

    print(f"总共创建了 {len(clips)} 条字幕")

    final_clip = CompositeVideoClip([video] + clips, size=video.size)

    print(f"开始写入最终视频文件: {output_path}")
    final_clip.write_videofile(output_path, codec="libx264", fps=video.fps)
    print("视频文件写入完成")


audio_path = "./res/12miao.mp4"
srt_path = "./res/12miao.srt"
output_video_path = "./res/output.mp4"

srt_path = transcribe_audio_to_srt(audio_path, srt_path, model_size="large-v2", device="cpu", compute_type="int8")
add_subtitles_to_video(audio_path, srt_path, output_video_path, subtitle_width_ratio=0.90, subtitle_y_position=280)
