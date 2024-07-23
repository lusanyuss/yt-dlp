import os
import subprocess

from yuliu.utils import get_mp4_duration, add_zimu_suffix, has_zimu_suffix, get_relative_path


def add_zimu_to_video(video_path, subtitles_path):
    if os.path.exists(video_path) and has_zimu_suffix(video_path):
        print(f"文件已存在且已添加字幕: {video_path}")
        return video_path

    font_file = 'ziti/fengmian/gwkt-SC-Black.ttf'  # 使用相对路径
    temp_output = os.path.join(os.path.dirname(video_path), "temp_output.mp4").replace("\\", "/")

    # 获取视频时长
    video_duration_ms = get_mp4_duration(video_path)
    video_duration_s = video_duration_ms / 1000  # 将毫秒转换为秒
    # 计算分钟数
    minutes_needed = video_duration_s / 60 / 4.3

    # 构建命令字符串，使用相对路径，并确保格式正确
    # 设置黄色的PrimaryColour值为&H00FFFF00
    primary_colour = '&H0000FFFF'
    outline_colour = '&H00000000'

    # 构建命令字符串，使用相对路径，并确保格式正确
    command = (
        f'ffmpeg -hwaccel cuda -i "{video_path}" -vf "subtitles=\'{get_relative_path(subtitles_path)}\':force_style='
        f'\'FontFile={font_file},FontSize=12,PrimaryColour={primary_colour},OutlineColour={outline_colour},Alignment=2\'" '
        f'-c:v h264_nvenc -c:a copy -y "{temp_output}"'
    )

    # 打印命令以便手动检查
    print("运行命令: \n\n", command)
    print(f"\n\n请耐心等待...大概需要 {minutes_needed:.2f} 分钟")
    try:
        # 使用 shell=True 执行命令字符串
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        result.check_returncode()  # 检查命令是否成功
        os.replace(temp_output, video_path)
        video_path = add_zimu_suffix(video_path)
        print(f"添加字幕成功")
    except Exception as e:
        print(f"发生错误: {e}\n输出: {result.stderr}")
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return video_path

    return video_path


if __name__ == '__main__':
    video_path = './release_video/aa测试目录/aa测试目录.mp4'
    temp_output = os.path.join(os.path.dirname(video_path), "temp_output.mp4").replace("\\", "/")
    if os.path.exists(temp_output):
        os.remove(temp_output)
    add_zimu_to_video(video_path, 'release_video/aa测试目录/aa测试目录_en.srt')
