import os
import shutil
import time

from moviepy.editor import VideoFileClip, concatenate_videoclips

import yt_dlp


class MyLogger:
    def debug(self, msg):
        if not msg.startswith('[debug] '):
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('下载完成，正在后处理 ...')


def format_selector(ctx):
    formats = ctx.get('formats')[::-1]
    best_video = next(f for f in formats if f['vcodec'] != 'none' and f['acodec'] == 'none')
    audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[best_video['ext']]
    best_audio = next(f for f in formats if f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == audio_ext)

    yield {
        'format_id': f'{best_video["format_id"]}+{best_audio["format_id"]}',
        'ext': best_video['ext'],
        'requested_formats': [best_video, best_audio],
        'protocol': f'{best_video["protocol"]}+{best_audio["protocol"]}'
    }


class PreProcessPP(yt_dlp.postprocessor.PostProcessor):
    def __init__(self, ydl, download_dir):
        super().__init__(ydl)
        self.download_dir = download_dir

    def run(self, info):
        self.to_screen('准备下载目录')

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            self.to_screen(f'创建目录: {self.download_dir}')

        info['start_time'] = time.time()

        return [], info


class PostProcessPP(yt_dlp.postprocessor.PostProcessor):
    def __init__(self, ydl, idx, download_dir, valid_videos):
        super().__init__(ydl)
        self.idx = idx
        self.download_dir = download_dir
        self.valid_videos = valid_videos

    def run(self, info):
        self.to_screen(f'处理下载的文件 {self.idx}')

        video_path = info['filepath']
        new_video_path = os.path.join(self.download_dir, f'{self.idx + 1}.mp4')

        if not video_path.endswith('.mp4'):
            self.to_screen('将视频转换为mp4格式')
            new_video_path_temp = video_path.replace('.webm', '.mp4')
            os.system(f'ffmpeg -i "{video_path}" "{new_video_path_temp}"')
            os.remove(video_path)
            shutil.move(new_video_path_temp, new_video_path)
        else:
            shutil.move(video_path, new_video_path)

        video = VideoFileClip(new_video_path)
        width, height = video.size

        if not (480 <= height <= 1080 and 854 <= width <= 1920):
            self.to_screen(f'视频分辨率 {width}x{height} 不在 480p 到 1080p 范围内')
            os.remove(new_video_path)
        else:
            self.valid_videos.append(new_video_path)

        end_time = time.time()
        total_time = end_time - info.get('start_time', end_time)
        self.to_screen(f'下载和处理完成，耗时 {total_time:.2f} 秒')

        return [], info


def download_videos(urls, dir_name):
    valid_videos = []
    for idx, url in enumerate(urls):
        ydl_opts = {
            'format': format_selector,
            'outtmpl': '%(title)s.%(ext)s',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_post_processor(PreProcessPP(ydl, f'download_cache/{dir_name}'), when='pre_process')
            ydl.add_post_processor(PostProcessPP(ydl, idx, f'download_cache/{dir_name}', valid_videos), when='post_process')
            ydl.download([url])

    if len(valid_videos) == len(urls):
        clips = [VideoFileClip(video) for video in valid_videos]
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(os.path.join(f'download_cache/{dir_name}', f'{dir_name}.mp4'), codec='libx264')

        # 删除源文件
        for video in valid_videos:
            os.remove(video)


if __name__ == '__main__':
    URLS = ['https://www.youtube.com/watch?v=BaW_jenozKc', 'https://www.youtube.com/watch?v=BaW_jenozKc']
    download_videos(URLS, 'aaa吃独食')
