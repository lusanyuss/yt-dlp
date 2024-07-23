import argparse
import glob
import os
import time
from pathlib import Path

from pydub import AudioSegment

# python inference.py --input_audio mixture1.wav mixture2.wav --output_folder ./results/
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="一个演示命令行参数的示例程序。")
    parser.add_argument('--input', type=str, default='input', help='输入文件夹')
    parser.add_argument('--output', type=str, default='output', help='输出文件夹')
    args = parser.parse_args()
    print(f"输入文件夹: {args.input}")
    print(f"输出文件夹: {args.output}")
    # 使用示例
    start_time = time.time()
    # python C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-CDX23-Cinematic-Sound-Demixing\mvsep_main.py --input C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-CDX23-Cinematic-Sound-Demixing\input\摊牌了,我有三个后妈 --output C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-CDX23-Cinematic-Sound-Demixing\output\摊牌了,我有三个后妈
    if Path(args.input).is_dir():
        file_paths = sorted(glob.glob(args.input + "/*"))[:]
        input_audio_args = ' '.join([f'"{path}"' for path in file_paths])
        Path(args.output).mkdir(parents=True, exist_ok=True)
        base_dir = os.path.join('C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-CDX23-Cinematic-Sound-Demixing')
        inference = os.path.join(base_dir, 'inference.py')
        input_dir = args.input
        output_dir = args.output
        os.system(f'python {inference} --input_audio {input_audio_args} --output_folder {args.output} --high_quality')
        # 遍历 input_dir 目录
        for input_file in os.listdir(input_dir):
            if input_file.endswith('.mp3'):
                base_filename = os.path.splitext(input_file)[0]
                # 定义要合并的两个文件路径
                dialog_path = os.path.join(output_dir, f"{base_filename}_dialog.wav")
                effect_path = os.path.join(output_dir, f"{base_filename}_effect.wav")
                # 合并 dialog 和 effect 文件
                if os.path.exists(dialog_path) and os.path.exists(effect_path):
                    dialog_audio = AudioSegment.from_wav(dialog_path)
                    effect_audio = AudioSegment.from_wav(effect_path)
                    combined_audio = dialog_audio.overlay(effect_audio)
                    # 导出合并后的音频文件
                    combined_path = os.path.join(output_dir, f"{base_filename}_vocals.wav")
                    combined_audio.export(combined_path, format="wav")
                    print(f"合成完成: {combined_path}")
                    # 保留的文件列表
                    files_to_keep = [f"{base_filename}_vocals.wav"]
                    # 遍历 output_dir 并删除不需要的文件
                    for output_file in os.listdir(output_dir):
                        if output_file.startswith(base_filename) and output_file not in files_to_keep:
                            file_to_delete = os.path.join(output_dir, output_file)
                            os.remove(file_to_delete)
                            print(f"删除文件: {file_to_delete}")
    print(f"=====去背景音乐耗时: {time.time() - start_time:.2f} seconds")
# input_dir = os.path.join(base_dir, 'input')
# output_dir = os.path.join(base_dir, 'output')
#
# input_dir 目录中有  out_times_00_audio.mp3  和  out_times_01_audio.mp3  等文件,
#
# output_dir目录中有对应的 input_dir目录中文件名称加后缀的文件,其中包括
# out_times_00_audio_dialog.wav
# out_times_00_audio_effect.wav
# out_times_00_audio_instrum.wav
# out_times_00_audio_instrum2.wav
# out_times_00_audio_music.wav
#
# 都是根据 input_dir 的名称加后缀的wav文件,input_dir中的每一个文件会有对应的这output_dir目录中的5个文件
#
# 这是现状,现在请你遍历 input_dir 目录,来循环执行代码逻辑
# 1,先合通过out_times_00_audio_dialog.wav和out_times_00_audio_effect.wav 合成 out_times_00_audio_vocals.wav,
# 2.删除output_dir目录中其他的4个只保留 out_times_00_audio_vocals.wav和out_times_00_audio_instrum.wav文件即可
