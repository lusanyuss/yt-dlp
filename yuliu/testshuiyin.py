import os
import subprocess

from yuliu.utils import get_mp4_duration


def add_watermark_to_video(video_path):
    font_file = 'ziti/fengmian/gwkt-SC-Black.ttf'  # 使用相对路径
    text = "爽剧风暴"
    temp_output = os.path.join(os.path.dirname(video_path), "temp_output.mp4").replace("\\", "/")

    # 获取视频时长
    video_duration_ms = get_mp4_duration(video_path)
    video_duration_s = video_duration_ms / 1000  # 将毫秒转换为秒
    # 计算分钟数
    minutes_needed = video_duration_s / 60 / 4.3
    # 构建命令字符串，使用相对路径，并确保格式正确
    command = (
        f'ffmpeg -hwaccel cuda -i "{video_path}" -vf "drawtext=fontfile=\'{font_file}\':text=\'{text}\':'
        f'fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable=\'between(t,0,{video_duration_s})\'" '
        f'-c:v h264_nvenc -c:a copy -y "{temp_output}"'
    )
    # 打印命令以便手动检查
    print("Running command: \n\n", command)
    # ffmpeg -hwaccel cuda -i "./release_video/aa测试目录/aa测试目录.mp4" -vf "drawtext=fontfile='ziti/fengmian/gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,56.086)'" -c:v h264_nvenc -c:a copy -y "./release_video/aa测试目录/temp_output.mp4"
    # ffmpeg -hwaccel cuda -i "./release_video/aa测试目录/aa测试目录.mp4" -vf "subtitles='release_video/aa测试目录/aa测试目录.srt':force_style='FontFile=ziti/fengmian/gwkt-SC-Black.ttf,FontSize=24,PrimaryColour=&H00FFFFFF&,OutlineColour=&H000000&,Alignment=2'" -c:v h264_nvenc -c:a copy -y "./release_video/aa测试目录/temp_output.mp4"
    # ffmpeg -hwaccel cuda -i "C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\aa测试目录.mp4" -vf "subtitles='C:\yuliu\workspace\yt-dlp\yuliu\release_video\aa测试目录\aa测试目录_en.srt':force_style='FontFile=ziti/fengmian/gwkt-SC-Black.ttf,FontSize=12,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Alignment=2'" -c:v h264_nvenc -c:a copy -y "C:/yuliu/workspace/yt-dlp/yuliu/release_video/aa测试目录/temp_output.mp4"

    print(f"\n\n请耐心等待...大概需要 {minutes_needed:.2f} 分钟")
    try:
        # 使用 shell=True 执行命令字符串
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        result.check_returncode()  # 检查命令是否成功
        os.replace(temp_output, video_path)
    except Exception as e:
        print(f"Error occurred: {e}")
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return video_path

    return video_path


if __name__ == '__main__':
    add_watermark_to_video('./release_video/aa测试目录/aa测试目录.mp4')

'''
ffmpeg -hwaccel cuda -i "C:/yuliu/workspace/yt-dlp/yuliu/release_video/aa测试目录/aa测试目录.mp4" -vf "subtitles='./yuliu/release_video/aa测试目录/aa测试目录_en.srt':force_style='FontFile=ziti/fengmian/gwkt-SC-Black.ttf,FontSize=12,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Alignment=2'" -c:v h264_nvenc -c:a copy -y "C:/yuliu/workspace/yt-dlp/yuliu/release_video/aa测试目录/temp_output.mp4"
ffmpeg -hwaccel cuda -i "release_video/aa测试目录/aa测试目录.mp4" -vf "subtitles='../yuliu/release_video/aa测试目录/aa测试目录_en.srt':force_style='FontFile=ziti/fengmian/gwkt-SC-Black.ttf,FontSize=24,PrimaryColour=&H00FFFFFF&,OutlineColour=&H000000&,Alignment=2'" -c:v h264_nvenc -c:a copy -y "release_video/aa测试目录/temp_output.mp4"

'''

