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

    def set_bool_to_cache(self, key, value, expire=None):
        """设置布尔值缓存
        :param key: 缓存的键
        :param value: 布尔值
        :param expire: 过期时间（秒），可选
        """
        if not isinstance(value, bool):
            raise ValueError("value 必须是布尔值")
        self.cache.set(key, str(value), expire=expire)

    def get_bool_from_cache(self, key):
        """获取布尔值缓存
        :param key: 缓存的键
        :return: 布尔值，如果缓存不存在，返回 False
        """
        value = self.cache.get(key, default="False")
        return value == "True"

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
