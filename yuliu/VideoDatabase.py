import hashlib
import sqlite3


class Video:
    def __init__(self, id=None, title=None, filepath=None, background_removed=False, uploaded=False, youtube_url=None):
        self.id = id
        self.title = title
        self.filepath = filepath
        self.background_removed = background_removed
        self.uploaded = uploaded
        self.youtube_url = youtube_url


class VideoDatabase:
    def __init__(self, db_name='videos.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS videos
                          (id TEXT PRIMARY KEY,
                           title TEXT,
                           filepath TEXT,
                           background_removed BOOLEAN,
                           uploaded BOOLEAN,
                           youtube_url TEXT)''')
        self.conn.commit()

    def calculate_md5(self, filepath):
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def add_video(self, video):
        video.id = self.calculate_md5(video.filepath)
        self.c.execute("INSERT INTO videos (id, title, filepath, background_removed, uploaded, youtube_url) VALUES (?, ?, ?, ?, ?, ?)",
                       (video.id, video.title, video.filepath, video.background_removed, video.uploaded, video.youtube_url))
        self.conn.commit()

    def get_video(self, video_id):
        self.c.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = self.c.fetchone()
        return Video(*row) if row else None

    def update_video(self, video):
        self.c.execute("UPDATE videos SET title = ?, filepath = ?, background_removed = ?, uploaded = ?, youtube_url = ? WHERE id = ?",
                       (video.title, video.filepath, video.background_removed, video.uploaded, video.youtube_url, video.id))
        self.conn.commit()

    def delete_video(self, video_id):
        self.c.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        self.conn.commit()

    def list_videos(self):
        self.c.execute("SELECT * FROM videos")
        rows = self.c.fetchall()
        return [Video(*row) for row in rows]

    def __del__(self):
        self.conn.close()


# 测试代码
if __name__ == "__main__":
    db = VideoDatabase()

    # 添加视频
    video1 = Video(title="Sample Video 1", filepath="/path/to/video1.mp4")
    db.add_video(video1)

    # 查询视频
    video_id = db.calculate_md5("/path/to/video1.mp4")
    video = db.get_video(video_id)
    print(f"Retrieved: {video.title}, {video.filepath}, {video.background_removed}, {video.uploaded}, {video.youtube_url}")

    # 更新视频
    video.title = "Updated Video 1"
    video.background_removed = True
    db.update_video(video)

    # 列出所有视频
    videos = db.list_videos()
    for v in videos:
        print(f"Video: {v.title}, {v.filepath}, {v.background_removed}, {v.uploaded}, {v.youtube_url}")

    # 删除视频
    db.delete_video(video_id)
