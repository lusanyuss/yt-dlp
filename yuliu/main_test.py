# 调用方法
from yuliu import common

if __name__ == "__main__":

    sub_directory = 'aa归来之非凡人生test'
    common.check_and_run(sub_directory=sub_directory,
                         cover_title=sub_directory,
                         juji_num=1,
                         split_time_min=20,
                         is_test=True,

                         is_get_cover=True,
                         is_get_video=True,
                         is_get_fanyi=True,
                         is_get_fanyi_other=True,

                         num_of_covers=1,
                         is_high_quality=True,
                         cover_title_split_postion=0
                         )
