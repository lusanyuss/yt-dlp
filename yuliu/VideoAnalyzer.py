import hashlib  # 导入用于哈希运算的模块
import json  # 导入用于处理JSON数据的模块
import subprocess  # 导入用于执行子进程的模块

from yuliu.DirectoryManager import DirectoryManager


class VideoAnalyzer:
    def __init__(self):
        # 初始化类属性
        self.ffmpeg_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffmpeg.exe'
        self.ffprobe_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffprobe.exe'
        self.ffplay_path = 'D:\\Android\\workspace\\yt-dlp\\yuliu\\01_utils\\ffplay.exe'
        self.directory_manager = DirectoryManager()

    # 使用ffprobe获取视频文件的信息
    def get_ffprobe_output(self, video_file_path):
        command = [self.ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_streams',
                   '-show_format', video_file_path]
        output = subprocess.check_output(command).decode('utf-8')
        return json.loads(output)  # 将输出从JSON格式解码为Python对象

    # 获取视频文件的内部信息
    def get_internal_video_info(self, video_file_path):
        print(f"video_file_path: {video_file_path}")
        ffprobe_output = self.get_ffprobe_output(video_file_path)
        print(f"ffprobe_output: {ffprobe_output}")
        try:
            video_info = ffprobe_output['streams'][0]  # 获取第一个流的信息
            fps = eval(video_info['r_frame_rate'])  # 获取帧速率
            metadata = video_info['tags'] if 'tags' in video_info else None  # 获取元数据
        except KeyError:
            raise Exception(f"Cannot read video info. ffprobe output: {ffprobe_output}")
        return fps, metadata  # 返回帧速率和元数据

    # 计算文件的MD5哈希值
    def calculate_md5(self, file_path):
        hash_md5 = hashlib.md5()  # 创建一个MD5哈希对象
        with open(file_path, 'rb') as f:  # 以二进制读模式打开文件
            for chunk in iter(lambda: f.read(4096), b''):  # 按块读取文件
                hash_md5.update(chunk)  # 更新哈希值
        return hash_md5.hexdigest()  # 返回16进制的哈希值

    # 获取视频的外部信息
    def get_external_video_info(self, video_id):
        video_id = video_id.replace(".mp4", "")  # 移除文件扩展名
        with open(f'{video_id}.info.json', 'r', encoding='utf-8') as f:  # 打开JSON信息文件
            info = json.load(f)
        with open(f'{video_id}.mp4', 'rb') as f:  # 以二进制读模式打开视频文件
            data = f.read()
            md5 = hashlib.md5(data).hexdigest()  # 计算视频文件的MD5哈希值

        # 返回视频的信息
        return {
            'title': info['title'],  # 标题
            'description': info['description'],  # 描述
            'thumbnail': info['thumbnail'],  # 缩略图
            'md5': md5  # MD5哈希值
        }
