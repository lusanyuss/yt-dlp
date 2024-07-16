import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor


def clear_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)


def process_audio_with_mvsep_mdx23_onebyone(audio_file):
    start_time = time.time()
    print(f"\n========================================处理音频文件: {os.path.basename(audio_file)}")

    mvsep_input_dir = os.path.join(os.getcwd(), 'MVSEP-MDX23-Colab_v2', 'input', 'aa测试目录')
    mvsep_output_dir = os.path.join(os.getcwd(), 'MVSEP-MDX23-Colab_v2', 'output', 'aa测试目录')
    download_directory_dir = os.path.join(os.getcwd(), 'download_directory', 'aa测试目录')

    # 清空目录
    clear_directory(mvsep_input_dir)
    clear_directory(mvsep_output_dir)

    shutil.copy(audio_file, mvsep_input_dir)
    input_file_audio = os.path.join(mvsep_input_dir, os.path.basename(audio_file))

    output_file_vocals = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_vocals.wav")
    output_file_instrum = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_instrum.wav")

    if not os.path.exists(output_file_vocals):
        try:
            original_directory = os.getcwd()
            os.chdir(os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2"))
            command = ['python', 'mvsep_main.py', '--input', input_file_audio, '--output', mvsep_output_dir]
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            os.chdir(original_directory)
        except Exception as e:
            # 如果这两个文件存在就删除掉
            print(f"处理音频文件时发生错误: {e}")
            print(f"删除残缺文件: \n{output_file_vocals}\n{output_file_instrum}\n")
            if os.path.exists(output_file_vocals):
                os.remove(output_file_vocals)
            if os.path.exists(output_file_instrum):
                os.remove(output_file_instrum)

    if os.path.exists(output_file_vocals):
        destination = shutil.copy(output_file_vocals, download_directory_dir)
        elapsed_time = time.time() - start_time
        print(f"除背景音乐耗时: {elapsed_time:.2f} 秒")

        return destination, output_file_instrum
    else:
        raise FileNotFoundError("输出目录中未找到 _vocals.wav 文件.")


def process_audio_with_mvsep_mdx23_onebyone1(audio_files):
    start_time = time.time()
    print(f"\n========================================处理音频文件")

    mvsep_input_dir = os.path.join(os.getcwd(), 'MVSEP-MDX23-Colab_v2', 'input', 'aa测试目录')
    mvsep_output_dir = os.path.join(os.getcwd(), 'MVSEP-MDX23-Colab_v2', 'output', 'aa测试目录')
    download_directory_dir = os.path.join(os.getcwd(), 'download_directory', 'aa测试目录')

    # 清空目录
    clear_directory(mvsep_input_dir)
    clear_directory(mvsep_output_dir)
    for audio_file in audio_files:
        shutil.copy(audio_file, mvsep_input_dir)

    # input_file_audio = os.path.join(mvsep_input_dir, os.path.basename(audio_file))

    # output_file_vocals = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_vocals.wav")
    # output_file_instrum = os.path.join(mvsep_output_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_instrum.wav")

    # if not os.path.exists(output_file_vocals):
    try:
        original_directory = os.getcwd()
        os.chdir(os.path.join(os.getcwd(), "MVSEP-MDX23-Colab_v2"))
        command = ['python', 'mvsep_main.py', '--input', mvsep_input_dir, '--output', mvsep_output_dir]
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        os.chdir(original_directory)
    except Exception as e:
        # 如果这两个文件存在就删除掉
        print(f"处理音频文件时发生错误: {e}")

    elapsed_time = time.time() - start_time
    print(f"除背景音乐耗时: {elapsed_time:.2f} 秒")


if __name__ == '__main__':
    audio_files = [
        "./download_cache/aa测试目录/part1.mp3",
        "./download_cache/aa测试目录/part2.mp3",
        "./download_cache/aa测试目录/part3.mp3",
        "./download_cache/aa测试目录/part4.mp3",
        "./download_cache/aa测试目录/part5.mp3"
    ]

    # 串行执行
    print("串行执行开始...")
    start_time = time.time()
    for audio_file in audio_files:
        vocals, instrum = process_audio_with_mvsep_mdx23_onebyone(audio_file)
        print(f"处理完成: {audio_file}")
        print(f"人声文件: {vocals}")
        print(f"伴奏文件: {instrum}")
    serial_elapsed_time = time.time() - start_time
    print(f"串行执行总耗时: {serial_elapsed_time:.2f} 秒")



    # 并行执行
    print("\n并行执行开始...")
    start_time = time.time()
    process_audio_with_mvsep_mdx23_onebyone1(audio_files)
    parallel_elapsed_time = time.time() - start_time
    print(f"并行执行总耗时: {parallel_elapsed_time:.2f} 秒")
