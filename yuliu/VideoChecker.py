import os
from urllib.parse import urlparse, parse_qs

from yuliu.DirectoryManager import DirectoryManager


class VideoChecker:

    def __init__(self):
        # 初始化类属性
        self.ffmpeg_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffmpeg.exe'
        self.ffprobe_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffprobe.exe'
        self.ffplay_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffplay.exe'
        self.directory_manager = DirectoryManager()

    @staticmethod
    def get_video_id_from_url(url):
        """从URL中提取video ID"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params['v'][0] if 'v' in query_params else None

    @staticmethod
    def is_video_exists_in_directory(video_id, directory):
        """检查目录中是否存在指定的video ID的MP4文件"""
        return f"{video_id}.mp4" in os.listdir(directory)
