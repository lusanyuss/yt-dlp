# 调用方法
import time

from yuliu.run_main import run_main


def check_and_run(sub_directory, video_name, cover_title, split_time_min,
                  crop_bottom,
                  crop_top,
                  is_only_download=False, is_test=False, is_get_video=False, num_of_covers=1,
                  is_get_cover=False, is_get_fanyi=False, cover_title_split_postion=0):
    start_time = time.time()
    run_main(sub_directory=sub_directory,
             video_name=video_name,
             cover_title=cover_title,
             split_time_min=split_time_min,
             crop_bottom=crop_bottom,
             crop_top=crop_top,
             is_only_download=is_only_download,
             is_test=is_test,
             is_get_video=is_get_video,
             num_of_covers=num_of_covers,
             is_get_cover=is_get_cover,
             is_get_fanyi=is_get_fanyi,
             cover_title_split_postion=cover_title_split_postion
             )
    print(f"\ncheck_and_run总耗时情况:{(time.time() - start_time)}")
