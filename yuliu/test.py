# 创建一个VideoData类
from yuliu.DiskCacheUtil import DiskCacheUtil


class VideoData:
    def __init__(self, md5, title, description, cover_image):
        self.md5 = md5
        self.title = title
        self.description = description
        self.cover_image = cover_image

    def __repr__(self):
        return f"VideoData(md5={self.md5}, title={self.title}, description={self.description}, cover_image={self.cover_image})"


# 示例用法
if __name__ == "__main__":
    cache_util = DiskCacheUtil()

    # 创建视频对象
    video = VideoData(
        md5='example_md5_hash',
        title='示例视频标题',
        description='这是一个示例视频的描述',
        cover_image='cover_image_url_or_path'
    )

    # 设置缓存
    cache_util.set_to_cache('video_key', video)
    cache_util.set_to_cache('video_key', video)

    # 获取缓存
    cached_video = cache_util.get_from_cache('video_key')
    print(f'缓存的对象: {cached_video}')

    # 关闭缓存
    cache_util.close_cache()
