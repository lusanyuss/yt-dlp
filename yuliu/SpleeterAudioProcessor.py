import subprocess


class SpleeterAudioProcessor:
    def __init__(self, input_path):
        self.input_path = "./download_cache/aa测试目录/2.mp3"

    # spleeter separate -p spleeter:2stems -o output ./download_cache/aa测试目录/output.mp3
    def separate_audio(self):
        try:
            command = [
                "spleeter", "separate",
                "-p", "spleeter:2stems",
                "-o", "output", self.input_path
            ]
            subprocess.run(command, check=True)
            print("音频分离成功")
        except subprocess.CalledProcessError as e:
            print(f"音频分离失败: {e}")


# 示例使用
processor = SpleeterAudioProcessor("./download_cache/aa测试目录/output.mp3")
processor.separate_audio()
print(f'分离后的音频文件路径: {"./out/2/vocals.wav"}')
