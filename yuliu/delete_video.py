import os
import shutil


def get_dir(base_dir, sub_directory=None):
    dir_path = os.path.join(os.getcwd(), base_dir)
    if sub_directory:
        dir_path = os.path.join(dir_path, sub_directory)
    return dir_path


def delete_dir(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
        print(f"已删除文件夹及其内容: {directory}")
    else:
        print(f"文件夹不存在: {directory}")


if __name__ == '__main__':
    sub_directory_list = [
        # '新版-护国神帅',
        # '玄门侠女',
        # '萌宝助攻我帮妈妈改嫁总裁大佬',
        # '逃婚当天我抓了个总裁过日子',
        # '隐秘的婚姻',
        # '我无敌于世间',
        # '当丑女遇上总裁',
        # '我的爷爷是大佬',
        # '鉴宝神婿'
    ]
    base_dirs = ["release_video",
                 os.path.join("MVSEP-MDX23-Colab_v2", "input"),
                 os.path.join("MVSEP-MDX23-Colab_v2", "output")
                 ]

    for sub_directory in sub_directory_list:
        for base_dir in base_dirs:
            dir_path = get_dir(base_dir, sub_directory)
            delete_dir(dir_path)
