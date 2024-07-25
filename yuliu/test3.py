import subprocess

command = [
    "ffmpeg",
    "-hwaccel", "cuda",
    "-i", "release_video/aa测试目录/aa测试目录.mp4",
    "-vf", "subtitles='release_video/aa测试目录/aa测试目录_eng.srt':force_style='FontFile=ziti/fengmian/gwkt-SC-Black.ttf,FontSize=12,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,Alignment=2,MarginV=30', drawtext=fontfile='ziti/fengmian/gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,50)'",
    "-c:v", "h264_nvenc",
    "-c:a", "copy",
    "-y",
    "release_video/aa测试目录/aa测试目录_zimu.mp4"
]

# 打开子进程并实时读取输出
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True, errors='ignore')

with open("ffmpeg_output.log", "w", encoding="utf-8", errors='ignore') as log_file:
    while True:
        output = process.stdout.readline()
        err_output = process.stderr.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())
            log_file.write(output)
        if err_output:
            print(err_output.strip())
            log_file.write(err_output)

print("日志已保存到 ffmpeg_output.log 文件中")
