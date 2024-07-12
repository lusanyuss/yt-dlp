import yt_dlp


class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')


if __name__ == '__main__':
    URLS = ['https://www.bilibili.com/video/BV1sc411D7kp/?spm_id_from=333.337.search-card.all.click&vd_source=34c946526337005bdabd03a6e52e4632']

    ydl_opts = {
        'logger': MyLogger(),
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'ffmpeg_location': 'D:\\ffmpeg\\bin\\ffmpeg.exe',
        'outtmpl': f'%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'progress_hooks': [my_hook],
        'ignoreerrors': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(URLS)
