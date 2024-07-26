import subprocess
import os
import time

class SpleeterAudioProcessor:
    def __init__(self, input_path):
        self.input_path = input_path
        self.output_dir = "output"
        self.output_file = os.path.join(self.output_dir, "2stems", "vocals.wav")

    def separate_audio(self):
        try:
            start_time = time.time()
            command = [
                "spleeter", "separate",
                "-p", "spleeter:2stems",
                "-o", self.output_dir,
                self.input_path
            ]
            subprocess.run(command, check=True)
            end_time = time.time()
            print(f"音频分离成功，耗时 {end_time - start_time:.2f} 秒")
        except subprocess.CalledProcessError as e:
            print(f"音频分离失败: {e}")

    def get_output_file(self):
        return self.output_file

# 示例使用
# processor = SpleeterAudioProcessor("./release_video/周太太今天太难哄/out_times_00_audio.mp3")
# processor.separate_audio()
# output_file = processor.get_output_file()
# print(f"分离后的音频文件路径: {output_file}")
