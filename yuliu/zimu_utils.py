import os

from yuliu.utils import get_mp4_duration, add_zimu_suffix, has_zimu_suffix, get_relative_path, CommandExecutor


def add_zimu_shuiyin_to_video(video_path, subtitles_path):
    dest_video_path = add_zimu_suffix(video_path)
    subtitles_path = get_relative_path(subtitles_path)
    if os.path.exists(dest_video_path) and has_zimu_suffix(dest_video_path):
        print(f"文件已存在且已添加字幕: {video_path}")
        return dest_video_path

    font_file = 'ziti/fengmian/gwkt-SC-Black.ttf'  # 使用相对路径
    text = "爽剧风暴"
    # 获取视频时长
    video_duration_ms = get_mp4_duration(video_path)
    video_duration_s = video_duration_ms / 1000  # 将毫秒转换为秒
    # 计算分钟数
    minutes_needed = video_duration_s / 60 / 4.3
    # 构建命令字符串，使用相对路径，并确保格式正确
    # 设置黄色的PrimaryColour值为&H00FFFF00
    primary_colour = '&H0000FFFF'
    outline_colour = '&H00000000'
    margin_v = 30  # 调整字幕离底部的距离

    command = (
        f'ffmpeg -hwaccel cuda -i "{video_path}" -vf "subtitles=\'{get_relative_path(subtitles_path)}\':force_style='
        f'\'FontFile={font_file},FontSize=12,PrimaryColour={primary_colour},OutlineColour={outline_colour},Alignment=2,MarginV={margin_v}\', '
        f'drawtext=fontfile=\'{font_file}\':text=\'{text}\':'
        f'fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable=\'between(t,0,{video_duration_s})\'" '
        f'-c:v h264_nvenc -c:a copy -y "{dest_video_path}"'
    )

    # 打印命令以便手动检查
    print("运行命令: \n", command)
    print(f"\n\n请耐心等待...大概需要 {minutes_needed:.2f} 分钟")
    try:
        # 使用 shell=True 执行命令字符串
        CommandExecutor.run_command(command)
        os.remove(video_path)
        print(f"添加字幕成功 {dest_video_path}")
    except Exception as e:
        print(f"发生错误: {e}\n")
        if os.path.exists(dest_video_path):
            os.remove(dest_video_path)
        return None

    return dest_video_path


if __name__ == '__main__':
    print("===============相对==================")
    video_path = 'release_video/aa测试目录/aa测试目录.mp4'
    srt_path = 'release_video/aa测试目录/aa测试目录_en.srt'

    # print("==============绝对===================")
    # video_path = os.path.abspath(video_path).replace("\\", "/")
    # srt_path = os.path.abspath(srt_path).replace("\\", "/")
    # print(video_path)
    # print(srt_path)
    # temp_output = os.path.join(os.path.dirname(video_path), "temp_output.mp4").replace("\\", "/")
    # if os.path.exists(temp_output):
    #     os.remove(temp_output)
    # add_zimu_to_video(video_path, get_relative_path(srt_path))

    print("==============在转相对===================")
    video_path = get_relative_path(video_path)
    srt_path = get_relative_path(srt_path)
    print(video_path)
    print(srt_path)
    add_zimu_shuiyin_to_video(video_path, srt_path)
