import os
import cv2
import tempfile
import shutil
import numpy as np
import yt_dlp
from skimage.metrics import structural_similarity as ssim

class SlideExtractor:
    def __init__(self, video_url, interval=5, similarity_threshold=0.9):
        self.video_url = video_url
        self.interval = interval
        self.similarity_threshold = similarity_threshold
        self.temp_dir = tempfile.mkdtemp()
        self.output_folder = os.path.join(os.getcwd(), "slides")
        self.video_path = os.path.join(self.temp_dir, "video.mp4")
        os.makedirs(self.output_folder, exist_ok=True)

    def download_video(self):
        try:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(self.temp_dir, 'video.%(ext)s'),
                'merge_output_format': 'mp4',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.video_url])

            # Rename the downloaded file to "video.mp4" for consistency
            for file in os.listdir(self.temp_dir):
                if file.endswith(".mp4"):
                    os.rename(os.path.join(self.temp_dir, file), self.video_path)
                    break
        except Exception as e:
            raise Exception(f"Error downloading video: {str(e)}")

    def extract_slides(self):
        try:
            self.download_video()
            cap = cv2.VideoCapture(self.video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            interval_frame = int(fps * self.interval)
            slide_count = 0
            last_frame = None

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                current_frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                if current_frame_number % interval_frame == 0:
                    if last_frame is None:
                        last_frame = frame
                        slide_path = os.path.join(self.output_folder, f"slide_{slide_count:03d}.png")
                        cv2.imwrite(slide_path, frame)
                        slide_count += 1
                    else:
                        grayA = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
                        grayB = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        sim, _ = ssim(grayA, grayB, full=True)
                        if sim < self.similarity_threshold:
                            slide_path = os.path.join(self.output_folder, f"slide_{slide_count:03d}.png")
                            cv2.imwrite(slide_path, frame)
                            slide_count += 1
                            last_frame = frame

            cap.release()
            return slide_count > 0
        except Exception as e:
            raise Exception(f"Error extracting slides: {str(e)}")

    def get_output_folder(self):
        return self.output_folder

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
