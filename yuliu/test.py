import os.path

from yuliu.utils import get_keyframes, segment_video_times, merge_videos, find_split_points

# Example usage
baseDir = os.path.join("download_cache", "mytest")
input_file = os.path.join(baseDir, '1.mp4')
output_pattern = os.path.join(baseDir, 'out_times_%02d.mp4')
merged_output = os.path.join(baseDir, 'merged_output.mp4')

# 获取关键帧位置
keyframes = get_keyframes(input_file)
print(f"关键帧位置: {keyframes}")

# =====================分割视频=====================
split_time = (50 - 1) * 1000  # 例如，每3秒分割一次
segment_times = find_split_points(keyframes, split_time)
print(f"segment_times: {segment_times}")
video_list = segment_video_times(input_file, segment_times, output_pattern)

# =====================合并视频=====================
merge_videos(video_list, merged_output)  # 合并输出文件（位于当前目录）
