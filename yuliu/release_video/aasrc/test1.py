import os

import ffmpeg


# def reencode_video(input_file, output_file, codec='h264', crf=23, preset='medium'):
#     """Reencode a video to ensure consistent parameters."""
#     ffmpeg.input(input_file).output(
#         output_file,
#         vcodec=codec,
#         crf=crf,
#         preset=preset,
#         acodec='aac',
#         strict='experimental'
#     ).run()
#
#
# def concat_videos(input_dir, output_file):
#     # 获取目录中的所有 mp4 文件，并按名称中的数字排序
#     files = sorted([f for f in os.listdir(input_dir) if f.endswith('.mp4') and f[:-4].isdigit()],
#                    key=lambda x: int(x[:-4]))
#
#     # 确保目录中有文件可处理
#     if not files:
#         raise ValueError("No mp4 files found in the directory")
#
#     # 创建一个临时目录来存储重新编码的视频
#     temp_dir = os.path.join(input_dir, 'temp')
#     os.makedirs(temp_dir, exist_ok=True)
#
#     # 对每个视频进行重新编码
#     reencoded_files = []
#     for file in files:
#         input_path = os.path.join(input_dir, file)
#         output_path = os.path.join(temp_dir, file)
#         reencode_video(input_path, output_path)
#         reencoded_files.append(output_path)
#
#     # 创建临时文件列表供 FFmpeg 使用
#     with open('filelist.txt', 'w', encoding='utf-8') as f:
#         for file in reencoded_files:
#             f.write(f"file '{file}'\n")
#
#     # 使用 FFmpeg 拼接视频，并启用 GPU 加速
#     (
#         ffmpeg
#         .input('filelist.txt', format='concat', safe=0)
#         .output(output_file, c='copy')
#         .global_args('-hwaccel', 'cuda')
#         .global_args('-hwaccel_output_format', 'cuda')
#         .run()
#     )
#
#     # 清理临时文件列表和临时目录
#     os.remove('filelist.txt')
#     for file in reencoded_files:
#         os.remove(file)
#     os.rmdir(temp_dir)
#
#     print(f"Concatenated video saved to {output_file}")
#     return output_file
