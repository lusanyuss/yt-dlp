import hashlib
import json
import struct
import subprocess
import time

from yuliu.DiskCacheUtil import DiskCacheUtil


class KeyFrameExtractor:
    def __init__(self, video_path, cache_util):
        self.video_path = video_path
        self.cache_util = cache_util
        self.frame_rate = self.get_frame_rate()

    @staticmethod
    def read_box(f):
        box_header = f.read(8)
        if len(box_header) < 8:
            return None, None, None
        size, box_type = struct.unpack(">I4s", box_header)
        return size, box_type, box_header

    @staticmethod
    def parse_box(f, size, level=0):
        keyframes_indices = []
        while size > 0:
            box_size, box_type, box_header = KeyFrameExtractor.read_box(f)
            if box_type is None:
                break

            if box_type == b'stss':
                version = int.from_bytes(f.read(1), byteorder='big')
                flags = int.from_bytes(f.read(3), byteorder='big')
                entry_count = int.from_bytes(f.read(4), byteorder='big')
                sample_numbers = [int.from_bytes(f.read(4), byteorder='big') for _ in range(entry_count)]
                keyframes_indices.extend(sample_numbers)
                return keyframes_indices

            elif box_type in [b'moov', b'trak', b'mdia', b'minf', b'stbl']:
                inner_size = box_size - 8
                result = KeyFrameExtractor.parse_box(f, inner_size, level + 1)
                if result is not None:
                    keyframes_indices.extend(result)
            else:
                if box_size == 1:
                    box_size = struct.unpack(">Q", f.read(8))[0]
                f.seek(box_size - 8, 1)

            size -= box_size
        return keyframes_indices

    def _indices_to_times(self, indices, frame_rate):
        # 计算每个index对应的时间间隔（秒）
        time_interval = 1 / frame_rate
        return [index * time_interval for index in indices]

    def extract_keyframes(self):
        try:
            with open(self.video_path, 'rb') as f:
                file_size = f.seek(0, 2)  # Move to the end of the file to get size
                f.seek(0)  # Reset to the start of the file
                keyframes_indices = KeyFrameExtractor.parse_box(f, file_size)
                print(f"Extracted keyframe indices: {keyframes_indices}")
                keyframes_times = self._indices_to_times(keyframes_indices, self.frame_rate)
                keyframes = [{"frame": str(index - 1), "pkt_pts_time": f"{time:.6f}"} for index, time in zip(keyframes_indices, keyframes_times)]
                return keyframes
        except Exception as e:
            print_red(f"Error: {e}")
        return None

    def get_keyframes(self):
        file_md5 = self.get_file_md5(self.video_path)
        cache_key = f"keyframes_{file_md5}_time"
        self.cache_util.delete_from_cache(cache_key)  # 删除缓存
        cached_keyframes = self.cache_util.get_from_cache(cache_key)

        if cached_keyframes is not None:
            print("从缓存中获取关键帧信息")
            return cached_keyframes

        command = [
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "frame=best_effort_timestamp_time,pict_type", "-of", "json", self.video_path
        ]
        print("Running command: ", ' '.join(command))
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

        if result.returncode != 0:
            print(f"Error output: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout)

        keyframes_data = json.loads(result.stdout)

        if 'frames' not in keyframes_data:
            raise ValueError("ffprobe输出不包含帧信息")

        keyframes = []
        for frame_index, frame in enumerate(keyframes_data['frames']):
            if frame.get('pict_type') == 'I':
                timestamp = frame.get('best_effort_timestamp_time')
                if timestamp is not None:
                    keyframes.append({
                        "frame": str(frame_index),
                        "pkt_pts_time": timestamp
                    })
                else:
                    print(f"帧信息缺少 'best_effort_timestamp_time': {frame}")

        self.cache_util.set_to_cache(cache_key, keyframes)
        return keyframes

    @staticmethod
    def get_file_md5(file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        md5_result = hash_md5.hexdigest()
        return md5_result

    def get_frame_rate(self):
        command = [
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=r_frame_rate", "-of", "json", self.video_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

        if result.returncode != 0:
            print(f"Error output: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)

        stream_data = json.loads(result.stdout)
        if 'streams' not in stream_data or len(stream_data['streams']) == 0:
            raise ValueError("ffprobe输出不包含流信息")

        r_frame_rate = stream_data['streams'][0]['r_frame_rate']
        num, denom = map(int, r_frame_rate.split('/'))
        return num / denom

    def get_video_info(self):
        command = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "json", self.video_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

        if result.returncode != 0:
            print(f"Error output: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout)

        video_info = json.loads(result.stdout)
        duration = float(video_info['format']['duration'])
        return duration


if __name__ == "__main__":
    # 使用示例
    video_path = './release_video/aa测试目录/1.mp4'
    cache_util = DiskCacheUtil()
    extractor = KeyFrameExtractor(video_path, cache_util)

    # 打印视频基本信息
    video_duration = extractor.get_video_info()
    print(f"Video duration: {video_duration} seconds")

    # 测试 extract_keyframes 方法
    start_time = time.time()
    keyframes = extractor.extract_keyframes()
    end_time = time.time()
    extract_keyframes_time = end_time - start_time

    print(f"Extracted keyframes: {keyframes}")
    print(f"Time taken by extract_keyframes: {extract_keyframes_time} seconds")

    print('================================================')
    # 测试 get_keyframes 方法
    start_time = time.time()
    keyframes1 = extractor.get_keyframes()
    end_time = time.time()
    get_keyframes_time = end_time - start_time

    print(f"Extracted keyframes1: {keyframes1}")
    print(f"Time taken by get_keyframes: {get_keyframes_time} seconds")
