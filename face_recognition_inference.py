import os
import time
import yaml
import glob
import shutil
from src.face_recognition import VideoFaceRecognition
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_PATH = 'config/face_recognition_config.yaml'


class Handler(FileSystemEventHandler):
    IMAGE_EXTENSIONS = ['jpg', 'png']

    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = config
        self.model = VideoFaceRecognition(
            config['frame_compression'],
            config['frame_skip'],
        )

    def on_any_event(self, event):
        if event.is_directory and event.event_type == 'modified':
            # Get created folder path
            input_folder_contents = os.listdir(event.src_path)
            created_folder_path = None
            for input_folder_item in input_folder_contents:
                if input_folder_item.startswith('waiting'):
                    os.rename(
                        event.src_path + '/' + input_folder_item,
                        event.src_path + '/' + input_folder_item.replace('waiting', 'processing'),
                    )
                    created_folder_path = event.src_path + '/' + input_folder_item.replace('waiting', 'processing')
            
            if created_folder_path is None:
                return
            
            # Get input paths
            input_video_path = glob.glob(f'{created_folder_path}/*.mp4')[0]
            input_image_paths = []
            for ext in self.IMAGE_EXTENSIONS:
                input_image_paths.extend(glob.glob(f'{created_folder_path}/*.{ext}'))
            # Generate output path
            output_video_path = os.path.normpath(input_video_path.replace('processing', 'ready')).split(os.sep)
            output_video_path = self.config['output_folder'] + '/' + os.sep.join(output_video_path[-2:])
            # Create output folder
            os.mkdir(os.sep.join(output_video_path.split(os.sep)[:-1]))
            # Process video
            self.model(
                input_video_path,
                input_image_paths,
                output_video_path,
            )
            # Delete input folder
            shutil.rmtree(created_folder_path)


class Listener:
    def __init__(self, config: dict):
        self.config = config
        self.observer = Observer()

    def run(self):
        event_handler = Handler(self.config)
        self.observer.schedule(event_handler, self.config['input_folder'], recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()

        self.observer.join()


if __name__ == '__main__':
    print('Reading config...')
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)

    print('Starting listener...')
    listener = Listener(config)
    listener.run()
