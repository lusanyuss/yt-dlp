import os
import random
import shutil

import cv2
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

from yuliu.utils import delete_file


class VideoFrameProcessor:
    def __init__(self, video_path, output_folder='frames', num_frames=8):
        self.video_path = video_path
        self.output_folder = os.path.join(os.path.dirname(video_path), output_folder)
        self.num_frames = num_frames
        self.engine = RapidOCR()

    def capture_random_frames(self):
        # 打开视频文件
        cap = cv2.VideoCapture(self.video_path)

        # 检查视频是否成功打开
        if not cap.isOpened():
            print(f"无法打开视频文件: {self.video_path}")
            return []

        # 获取视频的总帧数
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 检查视频是否包含帧
        if total_frames == 0:
            print(f"视频文件中没有帧: {self.video_path}")
            return []

        # 确保输出文件夹存在
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        frame_paths = []
        for i in range(self.num_frames):
            # 随机选择一个帧号
            frame_id = random.randint(0, total_frames - 1)

            # 设置视频帧位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

            # 读取帧
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(self.output_folder, f'frame_{i + 1}.jpg')
                cv2.imencode('.jpg', frame)[1].tofile(frame_path)  # 使用tofile方法保存带有汉字的路径
                if os.path.exists(frame_path):
                    frame_paths.append(frame_path)
                else:
                    print(f"无法保存帧 {frame_id} 到路径 {frame_path}")
            else:
                print(f"无法读取帧 {frame_id} from {self.video_path}")

        # 释放视频捕获对象
        cap.release()

        return frame_paths

    def get_image_results(self, frame_paths):
        image_results = []

        for img_path in frame_paths:
            if not os.path.exists(img_path):
                print(f"文件 {img_path} 不存在，跳过")
                continue
            result = self.engine(img_path)
            if result:
                image_results.append(result[0])
            else:
                image_results.append(None)

        return image_results

    def process_and_get_coordinates(self):
        frame_paths = self.capture_random_frames()
        if not frame_paths:
            print("没有截取到任何帧，无法进行OCR处理")
            return {}

        image_results = self.get_image_results(frame_paths)

        # 删除生成的图片和文件夹
        if os.path.exists(self.output_folder):
            shutil.rmtree(self.output_folder)

        coordinates = self.get_text_display_coordinates(image_results)
        return coordinates

    @staticmethod
    def get_text_display_coordinates(image_results, image_width=720, image_height=1280, threshold=0.5, offset=4):
        valid_images_counts = {'left': 0, 'top': 0, 'right': 0, 'bottom': 0, 'center': 0}
        coordinates = {'left': [], 'top': [], 'right': [], 'bottom': [], 'center': []}
        center_heights = []

        for result in image_results:
            if result is None:
                continue

            directions_found = {'left': False, 'top': False, 'right': False, 'bottom': False, 'center': False}

            for item in result:
                left_x = item[0][0][0]
                right_x = item[0][1][0]
                top_y = item[0][0][1]
                bottom_y = item[0][2][1]

                width = right_x - left_x
                height = bottom_y - top_y

                if width > height:
                    if not directions_found['top'] and bottom_y <= 100:
                        directions_found['top'] = True
                        coordinates['top'].append(bottom_y)

                    if not directions_found['bottom'] and image_height - top_y <= 100:
                        directions_found['bottom'] = True
                        coordinates['bottom'].append(top_y)

                    # 检测图片下半部分区域
                    if not directions_found['center'] and image_height / 2 <= top_y < image_height - 100:
                        directions_found['center'] = True
                        coordinates['center'].append(bottom_y)
                        center_heights.append(height)

                if height > width:
                    if not directions_found['left'] and right_x <= 100:
                        directions_found['left'] = True
                        coordinates['left'].append(right_x)

                    if not directions_found['right'] and image_width - left_x <= 100:
                        directions_found['right'] = True
                        coordinates['right'].append(left_x)

            for direction in directions_found:
                if directions_found[direction]:
                    valid_images_counts[direction] += 1

        results = {}
        if valid_images_counts['left'] / len(image_results) >= threshold and coordinates['left']:
            results['left'] = max(coordinates['left']) + offset
        else:
            results['left'] = 0

        if valid_images_counts['top'] / len(image_results) >= threshold and coordinates['top']:
            results['top'] = max(coordinates['top']) + offset
        else:
            results['top'] = 0

        if valid_images_counts['right'] / len(image_results) >= threshold and coordinates['right']:
            results['right'] = image_width - min(coordinates['right']) + offset
        else:
            results['right'] = 0

        if valid_images_counts['bottom'] / len(image_results) >= threshold and coordinates['bottom']:
            results['bottom'] = image_height - min(coordinates['bottom']) + offset
        else:
            results['bottom'] = 0

        if valid_images_counts['center'] / len(image_results) >= (threshold / 4) and coordinates['center']:
            results['center'] = min(coordinates['center'])
            results['center_height'] = max(center_heights)
        else:
            results['center'] = 0
            results['center_height'] = 0

        return results

    def capture_and_process_frames(self, n, crop_params):
        error_count = 0
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print(f"无法打开视频文件: {self.video_path}")
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            print(f"视频文件中没有帧: {self.video_path}")
            return []

        # 确保images文件夹相对于视频路径存在
        video_dir = os.path.dirname(self.video_path)
        images_folder = os.path.join(video_dir, 'images')
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)

        saved_frame_paths = []

        while error_count < n:
            frame_id = random.randint(0, total_frames - 1)
            frame_path = os.path.join(images_folder, f'frame_{error_count + 1}.jpg')

            # 检查是否已经存在当前编号的图片
            if os.path.exists(frame_path):
                print(f"缓存中已存在图片: {frame_path}")
                saved_frame_paths.append(frame_path)
                error_count += 1
                continue

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ret, frame = cap.read()
            if not ret:
                continue

            crop_left = int(crop_params.get('left', 0))
            crop_right = int(crop_params.get('right', 0))
            crop_top = int(crop_params.get('top', 0))
            crop_bottom = int(crop_params.get('bottom', 0))

            original_height, original_width = frame.shape[:2]

            # 计算裁剪后的图像尺寸
            new_width = original_width - crop_left - crop_right
            new_height = original_height - crop_top - crop_bottom
            if new_width <= 0 or new_height <= 0:
                print("裁剪尺寸过大，导致图像尺寸为非正值。")
                continue

            # 中间最大区域裁剪
            left = crop_left
            top = crop_top
            right = original_width - crop_right
            bottom = original_height - crop_bottom
            cropped_frame = frame[top:bottom, left:right]

            # 创建临时路径保存裁剪的帧用于检测
            temp_frame_path = os.path.join(video_dir, 'temp_frame.jpg')
            cv2.imencode('.jpg', cropped_frame)[1].tofile(temp_frame_path)  # 使用tofile方法保存带有汉字的路径

            if os.path.exists(temp_frame_path):
                result, elapse = self.engine(temp_frame_path)
                if not result:  # 判断result是否为空列表
                    error_count += 1

                    # 使用PIL放大裁剪后的图像到原始尺寸
                    cropped_image = Image.open(temp_frame_path)
                    resized_image = cropped_image.resize((original_width, original_height), Image.Resampling.LANCZOS)
                    resized_image.save(frame_path)

                    print(f"保存干净图片: {frame_path}")
                    saved_frame_paths.append(frame_path)
                delete_file(temp_frame_path)

        cap.release()
        return saved_frame_paths


if __name__ == '__main__':
    # 示例调用方法：
    video_path = 'release_video/无敌六皇子/test_video.mp4'
    processor = VideoFrameProcessor(video_path)

    # 获取文本显示坐标
    coordinates = processor.process_and_get_coordinates()
    print(coordinates)

    # 捕获并处理帧，并返回截图地址列表
    saved_frame_paths = processor.capture_and_process_frames(3, coordinates)
    print("保存的图片路径：", saved_frame_paths)
