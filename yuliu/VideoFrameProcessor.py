import os
import random
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "8192"


def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"删除文件: {file_path}")
    except OSError as e:
        print(f"删除文件时出错: {e}")


class VideoFrameProcessor:
    def __init__(self, video_path, output_folder='frames', num_frames=8):
        self.video_path = video_path
        self.output_folder = os.path.join(os.path.dirname(video_path), output_folder)
        self.num_frames = num_frames
        self.engine = RapidOCR()

    def capture_random_frames(self):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print(f"无法打开视频文件: {self.video_path}")
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames == 0:
            print(f"视频文件中没有帧: {self.video_path}")
            return []

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        frame_paths = []
        for i in range(self.num_frames):
            frame_id = random.randint(0, total_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(self.output_folder, f'frame_{i + 1}.jpg')
                cv2.imencode('.jpg', frame)[1].tofile(frame_path)
                if os.path.exists(frame_path):
                    frame_paths.append(frame_path)
                else:
                    print(f"无法保存帧 {frame_id} 到路径 {frame_path}")
            else:
                print(f"无法读取帧 {frame_id} from {self.video_path}")

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

    def process_frame_range(self, start, end, crop_params, images_folder, temp_folder, total_frames):
        frame_paths = []
        cap = cv2.VideoCapture(self.video_path)

        for index in range(start, end + 1):
            frame_path = os.path.join(images_folder, f"{index}.jpg")
            if os.path.exists(frame_path):
                print(f"缓存中已存在图片: {frame_path}")
                frame_paths.append(frame_path)
                continue

            while True:
                frame_id = random.randint(0, total_frames - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ret, frame = cap.read()
                if not ret:
                    continue

                crop_left = int(crop_params.get('left', 0))
                crop_right = int(crop_params.get('right', 0))
                crop_top = int(crop_params.get('top', 0))
                crop_bottom = int(crop_params.get('bottom', 0))

                original_height, original_width = frame.shape[:2]

                new_width = original_width - crop_left - crop_right
                new_height = original_height - crop_top - crop_bottom
                if new_width <= 0 or new_height <= 0:
                    print("裁剪尺寸过大，导致图像尺寸为非正值。")
                    continue

                left = crop_left
                top = crop_top
                right = original_width - crop_right
                bottom = original_height - crop_bottom
                cropped_frame = frame[top:bottom, left:right]

                temp_frame_path = os.path.join(temp_folder, f'temp_frame_{index}.jpg')
                cv2.imencode('.jpg', cropped_frame)[1].tofile(temp_frame_path)

                if os.path.exists(temp_frame_path):
                    result, elapse = self.engine(temp_frame_path)
                    if not result:
                        cropped_image = Image.open(temp_frame_path)
                        resized_image = cropped_image.resize((original_width, original_height), Image.Resampling.LANCZOS)
                        resized_image.save(frame_path)
                        frame_paths.append(frame_path)
                        os.remove(temp_frame_path)  # 删除临时文件
                        break
                    os.remove(temp_frame_path)  # 删除临时文件
        cap.release()
        return frame_paths

    def capture_and_process_frames(self, n, num_threads, crop_params):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print(f"无法打开视频文件: {self.video_path}")
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            print(f"视频文件中没有帧: {self.video_path}")
            return []

        cap.release()

        video_dir = os.path.dirname(self.video_path)
        images_folder = os.path.join(video_dir, 'images')
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)

        temp_folder = os.path.join(video_dir, 'temp_frames')
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        saved_frame_paths = []
        frames_per_thread = n // num_threads
        ranges = [(i * frames_per_thread + 1, (i + 1) * frames_per_thread) for i in range(num_threads)]
        # 如果不能整除，处理剩余部分
        if n % num_threads != 0:
            ranges[-1] = (ranges[-1][0], ranges[-1][1] + (n % num_threads))

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(self.process_frame_range, start, end, crop_params, images_folder, temp_folder, total_frames) for start, end in ranges]
            for future in as_completed(futures):
                saved_frame_paths.extend(future.result())

        # 删除临时文件夹
        shutil.rmtree(temp_folder)

        # 对保存的路径进行排序
        saved_frame_paths.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

        return saved_frame_paths


if __name__ == '__main__':
    video_path = 'release_video/aa测试目录/aa测试目录_nobgm.mp4'
    processor = VideoFrameProcessor(video_path)

    coordinates = processor.process_and_get_coordinates()
    print(coordinates)

    saved_frame_paths = processor.capture_and_process_frames(24, 4, coordinates)
    print("保存的图片路径：", saved_frame_paths)
