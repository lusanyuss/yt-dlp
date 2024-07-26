import os
import shutil
import time

from yuliu.utils import get_mp4_duration, add_zimu_suffix, has_zimu_suffix, get_relative_path, CommandExecutor


def read_output(pipe, log_file):
    for line in iter(pipe.readline, ''):
        print(line.strip())
        log_file.write(line)
    pipe.close()


def add_zimu_shuiyin_to_video(video_nobgm, subtitles_path):
    if not os.path.exists(video_nobgm):
        raise Exception("无背景音乐视频不存在")

    if not os.path.exists(subtitles_path):
        raise Exception("字幕不存在")

    video_final = add_zimu_suffix(video_nobgm)
    subtitles_path = get_relative_path(subtitles_path)
    if os.path.exists(video_final) and has_zimu_suffix(video_final):
        print(f"文件已存在且已添加字幕和水印: {video_nobgm}")
        return video_nobgm, video_final

    start_time = time.time()
    font_file = 'ziti/fengmian/gwkt-SC-Black.ttf'  # 使用相对路径
    text = "爽剧风暴"
    # 获取视频时长
    video_duration_ms = get_mp4_duration(video_nobgm)
    video_duration_s = video_duration_ms / 1000  # 将毫秒转换为秒
    # 计算分钟数
    minutes_needed = video_duration_s / 60 / 24
    # 构建命令字符串，使用相对路径，并确保格式正确
    # 设置黄色的PrimaryColour值为&H00FFFF00
    primary_colour = '&H0000FFFF'
    outline_colour = '&H00000000'
    margin_v = 30  # 调整字幕离底部的距离

    command = (
        f'ffmpeg -loglevel info -hwaccel cuda -i "{video_nobgm}" -vf "subtitles=\'{get_relative_path(subtitles_path)}\':force_style='
        f'\'FontFile={font_file},FontSize=12,PrimaryColour={primary_colour},OutlineColour={outline_colour},Alignment=2,MarginV={margin_v}\', '
        f'drawtext=fontfile=\'{font_file}\':text=\'{text}\':'
        f'fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable=\'between(t,0,{video_duration_s})\'" '
        f'-c:v h264_nvenc -c:a copy -y "{video_final}"'
    )

    # 打印命令以便手动检查
    print("运行命令,加字幕和水印: \n", command)
    print(f"请耐心等待...大概需要 {minutes_needed:.2f} 分钟")
    try:
        pattern = r"(frame=|Parsed_subtitles)"  # 只打印包含 "frame=" 或 "Parsed_subtitles" 的行
        CommandExecutor.run_command(command, pattern)
        print(f"\n\n添加水印和字幕成功{video_final}\n耗时: {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"添加字幕和水印失败,发生错误: {e}\n")
        if os.path.exists(video_final):
            os.remove(video_final)
        return None, None

    return video_nobgm, video_final


if __name__ == '__main__':
    print("===============相对==================")
    video_path = 'release_video/aa测试目录/aa测试目录.mp4'
    srt_path = 'release_video/aa测试目录/aa测试目录_eng.srt'
    result = 'release_video/aa测试目录/aa测试目录_zimu.mp4'

    shutil.copy2('download_cache/aa测试目录/1.mp4', video_path)

    if os.path.exists(result):
        os.remove(result)
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
