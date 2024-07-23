import os
import subprocess


def add_subtitles(video_path, subtitles, output_path, font_file):
    filter_str = ""
    for sub in subtitles:
        filter_str += (
            f"drawtext=fontfile='{font_file}':text='{sub['text']}':"
            f"fontcolor=white:fontsize=24:x=(w-text_w)/2:y=h-(text_h*2):"
            f"enable='between(t,{sub['start']},{sub['end']})',"
        )
    filter_str = filter_str.rstrip(',')

    command = (
        f'ffmpeg -i "{video_path}" -vf "{filter_str}" '
        f'-c:a copy -y "{output_path}"'
    )
    print(command)  # 打印命令用于调试
    subprocess.run(command, shell=True, check=True)


# 示例字幕数据
subtitles = [
    {"text": "Hello, World!", "start": 0, "end": 2},
    {"text": "This is a test.", "start": 3, "end": 5},
]

# 字体文件路径
title_font = os.path.join(os.getcwd(), 'ziti', 'hongleibanshu', 'hongleibanshu.ttf')

# 调用函数
add_subtitles(os.path.join(os.getcwd(), 'res', 'input.mp4'), subtitles, os.path.join(os.getcwd(), 'res', 'output.mp4'), title_font)
