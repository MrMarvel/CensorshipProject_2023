import sys
from pathlib import Path
p = Path().absolute()
sys.path.append(str(p))
import cv2
import numpy as np
from tqdm import tqdm
from src.utils.video import VideoIterator
from yolo5face.get_model import get_model
from src.utils.video import VideoIterator
from yolo5face.get_model import get_model
from moviepy.editor import VideoFileClip
from config import Config
from warnings import filterwarnings
filterwarnings('ignore')

config = Config()

class CensorModel:
    def __init__(self) -> None:
        self.load_model()
    
    def load_model(self):
        self.model = get_model("yolov5n", gpu=-1, target_size=512, min_face=24)
    
    def detect(self, input_file_path:str, output_file_path:str):
        video_iterator = VideoIterator(input_file_path)

        video_writer = cv2.VideoWriter(
            output_file_path,
            cv2.VideoWriter_fourcc(*'MP4V'),
            video_iterator.fps,
            (video_iterator.width, video_iterator.height),
        )

        for frame in tqdm(video_iterator):
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            boxes = self.model(frame)[0][0]

            if len(boxes) > 0:
                mask = np.zeros_like(frame) - 1
                for box in boxes:
                    mask[box[1]:box[3], box[0]:box[2]] = 0

                blurred_frame = cv2.GaussianBlur(frame, (45, 45), 0)
                frame = np.where(
                    mask==np.array([255, 255, 255]),
                    frame,
                    blurred_frame
                )
            
            video_writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        video_writer.release()
    
    def blure(self,input_file_path:str, output_file_path:str):
        input_clip = VideoFileClip(input_file_path)
        output_clip = VideoFileClip(output_file_path)
        output_clip = output_clip.set_audio(input_clip.audio)
        output_clip.write_videofile(
        'temp/result.mp4',
        codec='libx264', 
        audio_codec='aac', 
        temp_audiofile='temp-audio.m4a', 
        remove_temp=True,
    )
    
    def censore(
        self,
        input_file_path:str = config.input,
        output_file_path:str = config.output
    )->None:
        self.detect(input_file_path, output_file_path)
        self.blure(input_file_path, output_file_path)
        
    
if __name__ == '__main__':
    c = CensorModel()
    c.censore()
    