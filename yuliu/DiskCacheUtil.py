import diskcache as dc

class DiskCacheUtil:
    def __init__(self, cache_dir='tmp/cache'):
        self.cache = dc.Cache(cache_dir)

    def set_to_cache(self, key, value, expire=None):
        """设置缓存
        :param key: 缓存的键
        :param value: 缓存的值
        :param expire: 过期时间（秒），可选
        """
        self.cache.set(key, value, expire=expire)

    def get_from_cache(self, key, default=None):
        """获取缓存
        :param key: 缓存的键
        :param default: 默认值，如果缓存不存在，返回默认值
        :return: 缓存的值或默认值
        """
        return self.cache.get(key, default=default)

    def delete_from_cache(self, key):
        """删除缓存
        :param key: 缓存的键
        """
        if key in self.cache:
            del self.cache[key]

    def clear_cache(self):
        """清空所有缓存"""
        self.cache.clear()

    def close_cache(self):
        """关闭缓存"""
        self.cache.close()

# 示例用法
if __name__ == "__main__":
    cache_util = DiskCacheUtil()

    # 设置永久缓存
    cache_util.set_to_cache('example_number', 15000)

    # 获取缓存
    value = cache_util.get_from_cache('example_number')
    print(value)  # 输出: 15000

    # 删除缓存（如果需要）
    # cache_util.delete_from_cache('example_number')

    # 清空缓存（如果需要）
    # cache_util.clear_cache()

    # 关闭缓存
    cache_util.close_cache()
