import argparse
import glob
import os
import subprocess
from pathlib import Path


def separate_audio(input,
                   output,
                   output_format='FLAC',
                   Separation_mode='Vocals/Instrumental',
                   input_gain=0,
                   restore_gain_after_separation=False,
                   filter_vocals_below_50hz=False,
                   BigShifts=3,
                   BSRoformer_model='ep_317_1297',
                   weight_BSRoformer=10,
                   weight_InstVoc=4,
                   use_VitLarge=True,
                   weight_VitLarge=1,
                   use_InstHQ4=False,
                   weight_InstHQ4=2,
                   overlap_InstHQ4=0.1,
                   use_VOCFT=False,
                   weight_VOCFT=2,
                   overlap_VOCFT=0.1,
                   overlap_demucs=0.6
                   ):
    use_InstVoc_ = '--use_InstVoc'
    use_BSRoformer_ = '--use_BSRoformer'
    use_VOCFT_ = '--use_VOCFT' if use_VOCFT else ''
    use_VitLarge_ = '--use_VitLarge' if use_VitLarge else ''
    use_InstHQ4_ = '--use_InstHQ4' if use_InstHQ4 else ''
    restore_gain = '--restore_gain' if restore_gain_after_separation else ''
    vocals_only = '--vocals_only' if Separation_mode == 'Vocals/Instrumental' else ''
    filter_vocals = '--filter_vocals' if filter_vocals_below_50hz else ''

    if Path(input).is_file():
        file_path = input
        Path(output).mkdir(parents=True, exist_ok=True)
        os.system(f'python inference.py \
            --input_audio "{file_path}" \
            --large_gpu \
            --BSRoformer_model {BSRoformer_model} \
            --weight_BSRoformer {weight_BSRoformer} \
            --weight_InstVoc {weight_InstVoc} \
            --weight_InstHQ4 {weight_InstHQ4} \
            --weight_VOCFT {weight_VOCFT} \
            --weight_VitLarge {weight_VitLarge} \
            --overlap_demucs {overlap_demucs} \
            --overlap_VOCFT {overlap_VOCFT} \
            --overlap_InstHQ4 {overlap_InstHQ4} \
            --output_format {output_format} \
            --BigShifts {BigShifts} \
            --output_folder "{output}" \
            --input_gain {input_gain} \
            {filter_vocals} \
            {restore_gain} \
            {vocals_only} \
            {use_VitLarge_} \
            {use_VOCFT_} \
            {use_InstHQ4_} \
            {use_InstVoc_} \
            {use_BSRoformer_}')
    else:

        # python C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-MDX23-Colab_v2\mvsep_main.py --input C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-MDX23-Colab_v2\input\aa测试目录 --output C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-MDX23-Colab_v2\output\aa测试目录

        base_dir = os.path.join('C:\yuliu\workspace\yt-dlp\yuliu\MVSEP-MDX23-Colab_v2')
        inference = os.path.join(base_dir, 'inference.py')
        input_dir = args.input
        output_dir = args.output

        file_paths = sorted(glob.glob(input + "/*"))[:]
        input_audio_args = ' '.join([f'"{path}"' for path in file_paths])
        Path(output).mkdir(parents=True, exist_ok=True)
        os.system(f'python {inference} \
            --input_audio {input_audio_args} \
            --large_gpu \
            --BSRoformer_model {BSRoformer_model} \
            --weight_BSRoformer {weight_BSRoformer} \
            --weight_InstVoc {weight_InstVoc} \
            --weight_InstHQ4 {weight_InstHQ4} \
            --weight_VOCFT {weight_VOCFT} \
            --weight_VitLarge {weight_VitLarge} \
            --overlap_demucs {overlap_demucs} \
            --overlap_VOCFT {overlap_VOCFT} \
            --overlap_InstHQ4 {overlap_InstHQ4} \
            --output_format {output_format} \
            --BigShifts {BigShifts} \
            --output_folder "{output}" \
            --input_gain {input_gain} \
            {filter_vocals} \
            {restore_gain} \
            {vocals_only} \
            {use_VitLarge_} \
            {use_VOCFT_} \
            {use_InstHQ4_} \
            {use_InstVoc_} \
            {use_BSRoformer_}')
        for input_file in os.listdir(input_dir):
            if input_file.endswith('.mp3') or input_file.endswith('.m4a') or input_file.endswith('.aac'):
                base_filename = os.path.splitext(input_file)[0]
                files_to_keep = [f"{base_filename}_vocals.wav"]
                # 遍历 output_dir 并删除不需要的文件
                for output_file in os.listdir(output_dir):
                    if output_file.startswith(base_filename) and output_file not in files_to_keep:
                        file_to_delete = os.path.join(output_dir, output_file)
                        if os.path.exists(file_to_delete):
                            os.remove(file_to_delete)
                            print(f"删除文件: {file_to_delete}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="一个演示命令行参数的示例程序。")
    parser.add_argument('--input', type=str, default='input', help='输入文件夹')
    parser.add_argument('--output', type=str, default='output', help='输出文件夹')
    parser.add_argument('--is_test', action='store_true', help='是否为测试模式')
    args = parser.parse_args()
    print(f"    输入文件夹: {args.input}")
    print(f"    输出文件夹: {args.output}")
    # 检查 is_test 参数
    if args.is_test:
        print("运行在测试模式下")
        # 获取输入文件夹中的所有 .aac 文件
        file_paths = sorted(glob.glob(args.input + "/*.aac"))
        # 创建输出文件夹
        Path(args.output).mkdir(parents=True, exist_ok=True)
        # 遍历所有 .aac 文件并转换为 .wav 文件
        for file_path in file_paths:
            input_file = Path(file_path)
            # 检查输入文件是否存在
            if not input_file.exists():
                print(f"Error: Input file {input_file} does not exist.")
                continue
            output_file = Path(args.output) / (input_file.stem + '_vocals.wav')
            # 使用 ffmpeg 进行文件转换
            subprocess.run(['ffmpeg', '-i', str(input_file), str(output_file)], check=True)
            if args.is_test:
                print(f"Converted {input_file} to {output_file}")
        print("所有文件转换完成。")
    else:
        print("运行在正常模式下")
        separate_audio(
            input=args.input,
            output=args.output,
            output_format='FLAC',
            Separation_mode='Vocals/Instrumental',
            input_gain=0,
            restore_gain_after_separation=False,
            filter_vocals_below_50hz=False,
            BigShifts=3,
            BSRoformer_model='ep_317_1297',
            weight_BSRoformer=10,
            weight_InstVoc=4,
            use_VitLarge=True,
            weight_VitLarge=1,
            use_InstHQ4=False,
            weight_InstHQ4=2,
            overlap_InstHQ4=0.1,
            use_VOCFT=False,
            weight_VOCFT=2,
            overlap_VOCFT=0.1,
            overlap_demucs=0.6
        )
