# 调用方法
import os

from yuliu.run_main import run_main


def check_and_run(sub_directory, cover_title, juji_num, split_time_min, is_only_download=False, is_clear_cache=False, is_get_video=True, num_of_covers=1,
                  is_get_cover=False, is_get_fanyi=False, is_high_quality=False, cover_title_split_postion=0):
    video_template = '{}.mp4'
    # 生成所有视频文件的路径
    videos = [os.path.join('download_cache', sub_directory, video_template.format(i)) for i in range(1, juji_num + 1)]
    # 检查文件是否存在
    missing_files = [video for video in videos if not os.path.exists(video)]
    if missing_files:
        print("以下视频文件缺失:")
        for missing_file in missing_files:
            print(missing_file)
    else:
        # 检查文件数是否与juji_num相等
        if len(videos) == juji_num:
            # 运行命令，添加base_directory和sub_directory参数
            print(f"所有 {juji_num} 个视频文件均存在，准备执行命令。")
            run_main(sub_directory=sub_directory,
                     cover_title=cover_title,
                     videos=videos,
                     split_time_min=split_time_min,
                     is_only_download=is_only_download,
                     is_clear_cache=is_clear_cache,
                     is_get_video=is_get_video,
                     num_of_covers=num_of_covers,
                     is_get_cover=is_get_cover,
                     is_get_fanyi=is_get_fanyi,
                     is_high_quality=is_high_quality,
                     cover_title_split_postion=cover_title_split_postion
                     )
        else:
            print(f"视频文件数量({len(videos)})与指定的剧集数量({juji_num})不相等，无法继续执行。")


def download_only_videos(urls, sub_directory):
    for index, url in enumerate(urls, start=1):
        run_main(sub_directory=sub_directory, video_download_name=str(index), is_only_download=True, url=url)
