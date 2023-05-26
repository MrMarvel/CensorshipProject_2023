from typing import List
import os
from src.utils.video import VideoIterator
from moviepy.editor import VideoFileClip

import numpy as np
import cv2
import face_recognition
from tqdm.auto import tqdm


class VideoFaceRecognition:
    def __init__(
        self,
        frame_compression: float = 1.0,
        frame_skip: int = 1,
    ) -> None:
        self.frame_compression = frame_compression
        self.frame_skip = frame_skip
    
    def __call__(self, input_video_path: str, input_image_paths: List[str], output_video_path: str):
        print(f'Started processing video {input_video_path}')

        input_face_encodings = self.__get_input_encodings(input_image_paths)

        # Blur faces
        intermediate_video_path = input_video_path + '_intermediate.mp4'
        input_video_iterator = VideoIterator(input_video_path)
        output_video_writer = cv2.VideoWriter(
            intermediate_video_path,
            cv2.VideoWriter_fourcc(*'MP4V'),
            input_video_iterator.fps,
            (input_video_iterator.width, input_video_iterator.height),
        )
        self.__process_video(input_face_encodings, input_video_iterator, output_video_writer)

        # Copy sound
        input_clip = VideoFileClip(input_video_path)
        intermediate_clip = VideoFileClip(intermediate_video_path)

        intermediate_clip = intermediate_clip.set_audio(input_clip.audio)
        intermediate_clip.write_videofile(
            output_video_path,
            codec='libx264', 
            audio_codec='aac', 
            temp_audiofile='temp-audio.m4a', 
            remove_temp=True,
        )

        # Delete intermediate video
        os.remove(intermediate_video_path)

        print(f'Finished processing video {input_video_path}, saved output to {output_video_path}')
    
    def __get_input_encodings(self, input_image_paths: List[str]) -> List[np.array]:
        input_face_encodings = []
        for input_image_path in input_image_paths:
            input_image = face_recognition.load_image_file(input_image_path)
            input_face_encodings.extend(face_recognition.face_encodings(input_image))
        return input_face_encodings

    def __process_video(
        self,
        input_face_encodings: List[np.array],
        input_video_iterator: VideoIterator,
        output_video_writer: cv2.VideoWriter,
    ):
        known_faces = []

        for i, frame in enumerate(tqdm(input_video_iterator)):
            if i % self.frame_skip == 0:
                small_frame = cv2.cvtColor(
                    cv2.resize(frame, (0, 0), fx=1/self.frame_compression, fy=1/self.frame_compression),
                    cv2.COLOR_BGR2RGB
                )
                face_locations = face_recognition.face_locations(small_frame)
                face_encodings = face_recognition.face_encodings(small_frame, face_locations)

                known_faces = []
                for face_location, face_encoding in zip(face_locations, face_encodings):
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(input_face_encodings, face_encoding, tolerance=0.5)
                    if True not in matches:
                        known_faces.append(face_location)
            
            # Create mask for blurred faces
            mask = np.zeros_like(frame) - 1
            for top, right, bottom, left in known_faces:
                top *= self.frame_compression
                right *= self.frame_compression
                bottom *= self.frame_compression
                left *= self.frame_compression
                mask[top:bottom, left:right] = 0
            # Blur frame on mask
            blurred_frame = cv2.GaussianBlur(frame, (81, 81), 0)
            frame = np.where(
                mask==np.array([255, 255, 255]),
                frame,
                blurred_frame
            )

            # Write frame to output video
            output_video_writer.write(frame)

        output_video_writer.release()
