import json
import os
import subprocess

from prettytable import PrettyTable, ALL

from yuliu.DirectoryManager import DirectoryManager

table = PrettyTable(hrules=ALL)
table.set_style(12)  # 设置 wrap 模式


class VideoVerifier:
    def __init__(self):
        # 初始化类属性
        self.ffmpeg_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffmpeg.exe'
        self.ffprobe_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffprobe.exe'
        self.ffplay_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffplay.exe'
        self.directory_manager = DirectoryManager()

    def get_frame_count(self, video_file_path):
        command = [self.ffprobe_path, '-v', 'error', '-select_streams', 'v:0',
                   '-show_entries', 'stream=nb_frames', '-of',
                   'default=nokey=1:noprint_wrappers=1', video_file_path]
        result = subprocess.run(command, capture_output=True, text=True)
        return int(result.stdout)

    def verify_video(self, source_video_file_name, output_video_file_name):
        source_video_file_path = os.path.join(self.directory_manager.source_directory, source_video_file_name)
        output_video_file_path = os.path.join(self.directory_manager.output_directory, output_video_file_name)
        source_video_frame_count = self.get_frame_count(source_video_file_path)
        output_video_frame_count = self.get_frame_count(output_video_file_path)

        if output_video_frame_count == source_video_frame_count + 1:
            print("The output video has one more frame than the source video.")
        else:
            print("The output video does not have one more frame than the source video.")

    def get_video_info(self, video_path):
        command = [self.ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format',
                   '-show_streams', video_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return json.loads(result.stdout)

    def compare_videos(self, video_file1_path, video_file2_path):
        video_file1_path = os.path.join(self.directory_manager.source_directory, video_file1_path)
        video_file2_path = os.path.join(self.directory_manager.output_directory, video_file2_path)
        video1_info = self.get_video_info(video_file1_path)
        video2_info = self.get_video_info(video_file2_path)

        main_attributes = ['format_name', 'duration', 'bit_rate', 'nb_streams', 'size',
                           'start_time', 'probe_score']
        stream_attributes = ['codec_name', 'codec_long_name', 'profile', 'codec_type',
                             'width', 'height', 'sample_rate', 'channels', 'channel_layout',
                             'nb_frames', 'avg_frame_rate', 'r_frame_rate', 'pix_fmt',
                             'bits_per_raw_sample']

        # 比较主要属性
        print(f"Comparing videos '{video_file1_path}' and '{video_file2_path}'.")
        x = PrettyTable()
        x.field_names = ["Attribute", "Original Video", "Modified Video"]
        for key in main_attributes:
            if key in video1_info and key in video2_info and video1_info[key] != video2_info[key]:
                x.add_row([key, video1_info[key], video2_info[key]])
        print(x)

        # 比较每个流的属性
        for i, (stream1, stream2) in enumerate(zip(video1_info['streams'], video2_info['streams']),
                                               start=1):
            x = PrettyTable()
            x.field_names = [f"Attribute", f"Original Stream {i}", f"Modified Stream {i}"]
            for key in stream_attributes:
                if key in stream1 and key in stream2 and stream1[key] != stream2[key]:
                    x.add_row([key, stream1[key], stream2[key]])
            print(x)



