import tensorflow as tf


print("TensorFlow 版本:", tf.__version__)
print("CUDA 可用:", tf.test.is_built_with_cuda())
print("GPU 可用:", tf.config.list_physical_devices('GPU'))
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
'''
ffmpeg -hwaccel cuda -i "C:\yuliu\workspace\yt-dlp\yuliu\download_cache\aa测试目录\1.mp4" -vf "drawtext=fontfile='ziti/fengmian/gwkt-SC-Black.ttf':text='爽剧风暴':fontcolor=white@0.20:fontsize=70:x=W-tw-10:y=10:enable='between(t,0,55)'" -c:v h264_nvenc -c:a copy -y "C:/yuliu/workspace/yt-dlp/yuliu/download_cache/aa测试目录/1_.mp4"

'''
