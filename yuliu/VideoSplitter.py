import json
import subprocess


class VideoSplitter:
    def __init__(self):
        self.ffmpeg_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffmpeg.exe'
        self.ffprobe_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffprobe.exe'
        self.ffplay_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffplay.exe'

    # 确定视频的总时长
    def get_video_duration(self, video_path):
        cmd = [
            self.ffprobe_path,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = json.loads(result.stdout)['format']['duration']
        return float(duration)


    # 根据关键帧切割视频
    def split_video(self, video_with_keyframes, duration):
        segment_duration = duration / 3
        output_files = []

        for i in range(3):
            start_time = i * segment_duration
            output_file = f"02_source_directory/part{i + 1}.mp4"  # 修改这里
            cmd = [
                self.ffmpeg_path,
                '-i', video_with_keyframes,
                '-ss', str(start_time),
                '-t', str(segment_duration),
                '-c', 'copy',
                output_file
            ]
            subprocess.run(cmd)
            output_files.append(output_file)

        return output_files
