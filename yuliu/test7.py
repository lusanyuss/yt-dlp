import os

video_path = r'C:\yuliu\workspace\yt-dlp\yuliu\release_video\080_真假千金姐姐死后成为霸总白月光\真假千金姐姐死后成为霸总白月光_nobgm_final.mp4'

if os.path.exists(video_path):
    file_size = os.path.getsize(video_path)
    print(f"视频文件存在，大小为 {file_size} 字节")
else:
    print("视频文件不存在")

# 使用FFmpeg进行格式检查（需要安装FFmpeg）
import subprocess

def check_video_format(video_path):
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', video_path, '-f', 'null', '-'], stderr=subprocess.PIPE)
    if result.returncode == 0:
        print("视频文件格式正常")
    else:
        print(f"视频文件格式有误: {result.stderr.decode()}")


import subprocess

def get_video_info(video_path):
    command = [
        'ffmpeg', '-i', video_path, '-hide_banner'
    ]
    result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if result.returncode != 0:
        # ffmpeg 输出到 stderr，需要从 stderr 中获取信息
        print(result.stderr.decode())
    else:
        print(result.stdout.decode())

video_nobgm = r"C:\yuliu\workspace\yt-dlp\yuliu\release_video\080_真假千金姐姐死后成为霸总白月光\真假千金姐姐死后成为霸总白月光_nobgm.mp4"
# get_video_info(video_nobgm)


# check_video_format(video_nobgm)
check_video_format(video_path)
