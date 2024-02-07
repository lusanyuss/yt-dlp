import yt_dlp


class MyLogger:
    def debug(self, msg):
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        print(msg)

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('title:', d['filename'])


class YoutubeDownloader:
    def __init__(self, video_dir, logger=MyLogger(), progress_hooks=[my_hook]):
        self.video_dir = video_dir
        self.ydl_opts = {
            'logger': logger,
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'ffmpeg_location': 'D:\\ffmpeg\\bin\\ffmpeg.exe',
            'outtmpl': f'{self.video_dir}\\%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'progress_hooks': progress_hooks,
            'ignoreerrors': True
        }

    # 获取 标题，描述，封面，md5
    def download(self, url):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file_path = f"{self.video_dir}\\{info_dict['id']}.mp4"
            return video_file_path
