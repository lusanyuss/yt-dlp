# 调用方法
from yuliu import voice_utils
from yuliu.run_main import run_main


def check_and_run(sub_directory, cover_title,  split_time_min, is_only_download=False, is_test=False, is_get_video=False, num_of_covers=1,
                  is_get_cover=False, is_get_fanyi=False, cover_title_split_postion=0):
    run_main(sub_directory=sub_directory,
             cover_title=cover_title,
             split_time_min=split_time_min,
             is_only_download=is_only_download,
             is_test=is_test,
             is_get_video=is_get_video,
             num_of_covers=num_of_covers,
             is_get_cover=is_get_cover,
             is_get_fanyi=is_get_fanyi,
             cover_title_split_postion=cover_title_split_postion
             )

    voice_utils.play_voice_message(f'程序执行完毕!!!')


# else:
#     print(f"视频文件数量({len(videos)})与指定的剧集数量({juji_num})不相等，无法继续执行。")


def download_only_videos(urls, sub_directory):
    for index, url in enumerate(urls, start=1):
        run_main(sub_directory=sub_directory, video_download_name=str(index), is_only_download=True, url=url)
