import datetime
import os
from collections import Counter

import ffmpeg


def get_video_audio_info(file):
    probe = ffmpeg.probe(file)
    video_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    audio_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    return {
        "file": file,
        "video_codec": video_info['codec_name'] if video_info else "无",
        "width": video_info['width'] if video_info else "无",
        "height": video_info['height'] if video_info else "无",
        "audio_codec": audio_info['codec_name'] if audio_info else "无",
        "sample_rate": audio_info['sample_rate'] if audio_info else "无",
        "channels": audio_info['channels'] if audio_info else "无"
    }


def get_most_common_format(infos):
    video_codecs = Counter([info["video_codec"] for info in infos])
    resolutions = Counter([(info["width"], info["height"]) for info in infos])
    audio_codecs = Counter([info["audio_codec"] for info in infos])
    sample_rates = Counter([info["sample_rate"] for info in infos])
    channels = Counter([info["channels"] for info in infos])

    return {
        "video_codec": video_codecs.most_common(1)[0][0],
        "resolution": resolutions.most_common(1)[0][0],
        "audio_codec": audio_codecs.most_common(1)[0][0],
        "sample_rate": sample_rates.most_common(1)[0][0],
        "channels": channels.most_common(1)[0][0]
    }


def convert_video_to_match(file, target_format, output_file):
    print(f"Converting {file} to match target format...")
    try:
        (
            ffmpeg
            .input(file)
            .output(output_file, vf=f"scale={target_format['resolution'][0]}:{target_format['resolution'][1]}",
                    vcodec='libx264', acodec='aac', ar=target_format['sample_rate'], ac=target_format['channels'],
                    video_bitrate='5000k', audio_bitrate='192k', preset='fast')  # 强制设置帧率
            .run(quiet=True)
        )
        print(f"Conversion successful: {output_file}")
    except ffmpeg.Error as e:
        print(f"Conversion failed for {file} with error: {e}")
        raise


def concatenate_videos_with_copy(video_files, output_file):
    with open('filelist.txt', 'w') as filelist:
        for file in video_files:
            filelist.write(f"file '{file}'\n")

    temp_output = "temp_merged.mp4"
    (
        ffmpeg
        .input('filelist.txt', format='concat', safe=0)
        .output(temp_output, c='copy')
        .run(quiet=True)
    )

    os.remove('filelist.txt')

    # 重新封装处理
    print("Re-wrapping the merged video...")
    (
        ffmpeg
        .input(temp_output)
        .output(output_file, vcodec='copy', acodec='copy')
        .run(quiet=True)
    )

    os.remove(temp_output)


def get_creation_time(file):
    return os.path.getctime(file)


def merge_mp4_files(directory):
    video_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp4')]

    if not video_files:
        print("No mp4 files found in the directory.")
        return

    # 获取文件格式信息
    infos = [get_video_audio_info(file) for file in video_files]

    # 获取最常见的格式和分辨率
    most_common_format = get_most_common_format(infos)
    print(f"Most common format: {most_common_format}")

    # 检查并转换格式不一致的文件
    converted_files = []
    for info in infos:
        if (info["video_codec"] != most_common_format["video_codec"] or
            (info["width"], info["height"]) != most_common_format["resolution"] or
            info["audio_codec"] != most_common_format["audio_codec"] or
            info["sample_rate"] != most_common_format["sample_rate"] or
            info["channels"] != most_common_format["channels"]):
            converted_file = os.path.join(directory, f"converted_{os.path.basename(info['file'])}")
            convert_video_to_match(info["file"], most_common_format, converted_file)
            if os.path.exists(converted_file):
                converted_files.append(converted_file)
            else:
                print(f"Converted file not found: {converted_file}")
        else:
            converted_files.append(info["file"])

    # 获取原始视频和转换后视频的创建时间顺序
    original_files_sorted = sorted(video_files, key=get_creation_time)
    converted_files_sorted = sorted(converted_files, key=get_creation_time)

    print("\n原始视频集合的创建时间顺序：")
    for file in original_files_sorted:
        print(f"{file} - {datetime.datetime.fromtimestamp(get_creation_time(file))}")

    print("\n转换后视频集合的创建时间顺序：")
    for file in converted_files_sorted:
        print(f"{file} - {datetime.datetime.fromtimestamp(get_creation_time(file))}")

    # 使用copy的方式合并所有文件
    output_file = os.path.join(directory, "merged_output.mp4")
    concatenate_videos_with_copy(converted_files_sorted, output_file)
    print(f"Merged video saved as {output_file}")


if __name__ == "__main__":
    directory = "download_cache"  # 替换为你的文件夹路径
    merge_mp4_files(directory)
