import json
import subprocess
import time

from yuliu.DiskCacheUtil import DiskCacheUtil
from yuliu.utils import get_file_md5, execution_time


@execution_time
def extract_keyframes(input_file, cache_util):
    file_md5 = get_file_md5(input_file)
    cache_key = f"keyframes_{file_md5}"
    cached_keyframes = cache_util.get_from_cache(cache_key)

    if cached_keyframes is not None:
        print("从缓存中获取关键帧信息")
        return cached_keyframes

    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "frame=best_effort_timestamp_time,pict_type", "-of", "json", input_file
    ]
    print("Running command: ", ' '.join(command))
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

    if result.returncode != 0:
        print(f"Error output: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)

    keyframes_data = json.loads(result.stdout)

    if 'frames' not in keyframes_data:
        raise ValueError("ffprobe输出不包含帧信息")

    keyframes = []
    for frame in keyframes_data['frames']:
        if frame.get('pict_type') == 'I':
            timestamp = frame.get('best_effort_timestamp_time')
            if timestamp is not None:
                keyframes.append({
                    "frame": timestamp,
                    "pkt_pts_time": timestamp
                })
            else:
                print(f"帧信息缺少 'best_effort_timestamp_time': {frame}")

    cache_util.set_to_cache(cache_key, keyframes)
    return keyframes


input_file = "C:\\yuliu\\workspace\\yt-dlp\\yuliu\\download_directory\\aa测试目录\\5fenzhong.mp4"
start_time = time.time()  # 开始时间

cache_util = DiskCacheUtil()

keyframes = extract_keyframes(input_file, cache_util)
print("关键帧信息: ", keyframes)

cache_util.close_cache()

end_time = time.time()  # 结束时间
print(f"方法执行时间: {end_time - start_time:.2f} 秒")

# 示例用法
