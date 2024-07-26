import os
import subprocess
import time

from pydub import AudioSegment


def process_audio_with_spleeter(file_path):
    output_dir = './output'
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_subdir = os.path.join(output_dir, base_name)
    if os.path.exists(output_subdir):
        print(f"output_directory {output_subdir} 已存在，跳过spleeter处理。")
        return

    command = ['spleeter', 'separate', '-p', 'spleeter:2stems', '-o', output_dir, file_path]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"spleeter处理完成，输出目录为：{output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"spleeter处理失败: {e}")


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')


def check_and_convert_to_mp3(audio_file):
    if not audio_file.lower().endswith('.mp3'):
        raise ValueError("文件不是MP3格式，需要转换。")
    return audio_file


def split_mp3(processed_audio_file, max_duration=600000):
    song = AudioSegment.from_mp3(processed_audio_file)
    duration = len(song)
    parts = duration // max_duration + (1 if duration % max_duration > 0 else 0)
    split_files = []
    for part in range(parts):
        start, end = part * max_duration, min((part + 1) * max_duration, duration)
        split_part = song[start:end]
        split_file_path = f"{processed_audio_file[:-4]}_part{part + 1}.mp3"
        split_part.export(split_file_path, format="mp3")
        split_files.append(split_file_path)
    return split_files


def merge_vocals(split_files, audio_file, video_file):
    vocals_all = AudioSegment.empty()
    for split_file in split_files:
        # Assuming the vocals.wav files are stored in a specific structure
        vocals_path = f"output/{os.path.basename(split_file)[:-4]}/vocals.wav"
        vocals_segment = AudioSegment.from_wav(vocals_path)
        vocals_all += vocals_segment

    # Use the base name of the video file (which is the ID) for output naming
    file_id = os.path.splitext(os.path.basename(video_file))[0]  # Removes extension

    output_dir = f"output/{file_id}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    vocals_output_path = os.path.join(output_dir, f"{file_id}_vocals_all.wav")
    vocals_all.export(vocals_output_path, format="wav")

    merged_video_path = os.path.join(output_dir, f"{file_id}_final_output.mp4")
    if os.path.exists(merged_video_path):
        print(f"Merged video file {merged_video_path} already exists. Using the existing merged video.")
        return merged_video_path

    command = ['ffmpeg', '-y', '-i', video_file, '-i', vocals_output_path, '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', merged_video_path]
    command += ['-loglevel', 'quiet']
    subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
    print(f"Merged video saved to: {merged_video_path}")
    return merged_video_path


def separate_audio_and_video(video_path):
    base, _ = os.path.splitext(video_path)
    audio_output, video_output = f"{base}_audio.mp3", f"{base}_video.mp4"
    if not os.path.exists(audio_output):
        command = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'libmp3lame', audio_output]
        command += ['-loglevel', 'quiet']
        subprocess.run(command,check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"Audio extracted to: {audio_output}")
    if not os.path.exists(video_output):
        command = ['ffmpeg', '-i', video_path, '-an', '-vcodec', 'copy', video_output]
        command += ['-loglevel', 'quiet']
        subprocess.run(command,check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"Video extracted to: {video_output}")
    return audio_output, video_output


def process_video_file(video_file):
    audio_file, video_file = separate_audio_and_video(video_file)
    processed_audio_file = check_and_convert_to_mp3(audio_file)
    split_files = split_mp3(processed_audio_file)
    for split_file in split_files:
        process_audio_with_spleeter(split_file)
    return merge_vocals(split_files, audio_file, video_file)


def merge_videos(video_files, output_dir, max_length=50):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filelist_path = os.path.join(output_dir, 'filelist.txt')
    with open(filelist_path, 'w') as filelist:
        for video_file in video_files:
            filelist.write(f"file '{os.path.abspath(video_file)}'\n")

    base_output_filename = '_'.join([os.path.splitext(os.path.basename(v))[0] for v in video_files])
    if len(base_output_filename) > max_length:
        base_output_filename = 'merged_' + str(int(time.time()))
    output_filename = base_output_filename + '.mp4'
    merged_video_path = os.path.join(output_dir, output_filename)
    command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', filelist_path, '-c', 'copy', merged_video_path]
    command += ['-loglevel', 'quiet']
    subprocess.run(command,check=True, capture_output=True, text=True, encoding='utf-8')
    print(f"Merged video saved to: {merged_video_path}")
    os.remove(filelist_path)


if __name__ == '__main__':
    # 检查下载目录中的最新文件
    download_path = 'release_video'  # 请根据实际情况替换
    # 定义视频文件列表，现在包含完整路径
    video_files = [
        os.path.join(download_path, 'BV12e411a7ys.mp4')
    ]
    processed_videos = [process_video_file(vf) for vf in video_files]
    output_dir = 'output_directory'
    merge_videos(processed_videos, output_dir)
