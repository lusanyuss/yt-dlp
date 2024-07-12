import argparse
import glob
import os
from pathlib import Path


def separate_audio(input,
                   output,
                   output_format='PCM_16',
                   Separation_mode='Vocals/Instrumental',
                   input_gain=0,
                   restore_gain_after_separation=False,
                   filter_vocals_below_50hz=False,
                   BigShifts=1,  # 优先速度，设置为较低值
                   BSRoformer_model='ep_317_1297',  # 使用快速模型
                   weight_BSRoformer=0,  # 降低权重以加快处理
                   weight_InstVoc=0,  # 降低权重以加快处理
                   use_VitLarge=False,  # 不使用VitLarge模型以提高速度
                   weight_VitLarge=0,
                   use_InstHQ4=False,  # 不使用InstHQ4模型以提高速度
                   weight_InstHQ4=0,
                   overlap_InstHQ4=0,
                   use_VOCFT=False,  # 不使用VOCFT模型以提高速度
                   weight_VOCFT=0,
                   overlap_VOCFT=0,
                   overlap_demucs=0.6  # Demucs仅在4-STEMS模式下使用
                   ):
    use_InstVoc_ = ''
    use_BSRoformer_ = '--use_BSRoformer'
    use_VOCFT_ = ''
    use_VitLarge_ = ''
    use_InstHQ4_ = ''
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
        file_paths = sorted(glob.glob(input + "/*"))[:]
        input_audio_args = ' '.join([f'"{path}"' for path in file_paths])
        Path(output).mkdir(parents=True, exist_ok=True)
        os.system(f'python inference.py \
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="一个演示命令行参数的示例程序。")
    parser.add_argument('--input', type=str, default='input', help='输入文件夹')
    parser.add_argument('--output', type=str, default='output', help='输出文件夹')
    args = parser.parse_args()
    print(f"输入文件夹: {args.input}")
    print(f"输出文件夹: {args.output}")
    # 使用示例
    separate_audio(
        input=args.input,
        output=args.output,
        output_format='PCM_16',  # 使用PCM_16格式以加快处理速度
        Separation_mode='Vocals/Instrumental',  # 仅分离人声
        input_gain=0,
        restore_gain_after_separation=False,
        filter_vocals_below_50hz=False,
        BigShifts=1,  # 优先速度
        BSRoformer_model='ep_317_1297',
        weight_BSRoformer=0,  # 降低权重以加快处理
        weight_InstVoc=0,  # 降低权重以加快处理
        use_VitLarge=False,  # 不使用VitLarge模型以提高速度
        weight_VitLarge=0,
        use_InstHQ4=False,  # 不使用InstHQ4模型以提高速度
        weight_InstHQ4=0,
        overlap_InstHQ4=0,
        use_VOCFT=False,  # 不使用VOCFT模型以提高速度
        weight_VOCFT=0,
        overlap_VOCFT=0,
        overlap_demucs=0.6  # Demucs仅在4-STEMS模式下使用
    )
