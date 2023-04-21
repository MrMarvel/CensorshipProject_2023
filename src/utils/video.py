from os import path

import cv2


class VideoIterator:
    def __init__(self, file_path: str) -> None:
        if not path.isfile(file_path):
            raise 

        self.cap = cv2.VideoCapture(file_path)

        self.length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def __len__(self) -> int:
        return self.length
    
    def __iter__(self):
        return self

    def __next__(self):
        ret, frame = self.cap.read()

        if ret == False:
            self.cap.release()
            raise StopIteration
        else:
            return frame
