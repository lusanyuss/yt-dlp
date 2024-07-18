import yt_dlp


class MyLogger:
    def debug(self, msg):
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
    URLS = ['https://www.bilibili.com/video/BV1h1421k7Mh/?spm_id_from=333.1007.tianma.1-2-2.click']

    video_path = './download_cache/src/1.mp4'
    ydl_opts = {
        'outtmpl': video_path,
        'logger': MyLogger(),
        # 'format': 'bv*+ba/b',
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'cookiesfrombrowser': ('chrome', None),
        'ffmpeg_location': 'D:\\ffmpeg\\bin\\ffmpeg.exe',
        # 'outtmpl': f'%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'progress_hooks': [my_hook],
        'ignoreerrors': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(URLS)
