import os
import yaml
import time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import cv2

CONFIG_PATH = 'config/bot_config.yaml'


def get_video_frame_cnt(video_file_path: str) -> int:
    video = cv2.VideoCapture(video_file_path)
    return video.get(cv2.CAP_PROP_FRAME_COUNT)


# Load config
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)
# Initialize bot
storage = MemoryStorage()
bot = Bot(config['token'])
dp = Dispatcher(bot, storage=storage)

# Create states
class States(StatesGroup):
    input_video = State()
    input_image = State()
    processing = State()


@dp.message_handler(commands='start')
async def start_handler(message: types.Message, state: FSMContext):
    # Set state
    await States.input_video.set()
    # Send message
    await message.answer(config['start_message'])
    await message.answer(config['input_video_help_message'])

@dp.message_handler(content_types=['video'], state=States.input_video)
async def video_handler(message: types.Message, state: FSMContext):
    # Create user folder
    user_folder_path = os.path.join(config['input_folder'], f'loading_{message.from_id}')
    os.mkdir(user_folder_path)
    # Get video file path
    video_file_path = await bot.get_file(message.video.file_id)
    print(video_file_path)
    # Download video file
    await bot.download_file(
        video_file_path,
        os.path.join(user_folder_path, 'video.mp4'),
    )

    # Change state
    await States.input_image.set()
    # Send message
    await message.answer(config['input_image_help_message'])
    await message.answer(config['start_processing_help_message'])

@dp.message_handler(content_types=['photo'], state=States.input_image)
async def image_handler(message: types.Message, state: FSMContext):
    # Get user folder path
    user_folder_path = os.path.join(config['input_folder'], str(message.from_id))
    # Download image file
    image_file_path = os.path.join(user_folder_path, f'image_{round(time.time()*1000)}.jpg')
    await message.photo[-1].download(image_file_path)

@dp.message_handler(commands='start_processing', state=States.input_image)
async def processing_handler(message: types.Message, state: FSMContext):
    # Get user folder path
    user_folder_path = os.path.join(config['input_folder'], str(message.from_id))
    # Rename user folder
    os.rename(
        user_folder_path,
        user_folder_path.rename('loading', 'waiting'),
    )

    # Change state
    await States.processing.set()
    # Estimate wait time (in minutes)
    video_file_path = os.path.join(user_folder_path, 'video.mp4')
    estimated_time = round(get_video_frame_cnt(video_file_path) / 24 / 60)
    # Send message
    await message.answer(
        config['start_processing_message'].format(estimated_time=estimated_time)
    )

@dp.message_handler(state=States.input_video)
async def error_video_handler(message: types.Message, state: FSMContext):
    # Send message
    await message.answer(config['input_video_help_message'])

@dp.message_handler(state=States.input_image)
async def error_video_handler(message: types.Message, state: FSMContext):
    # Send message
    await message.answer(config['input_image_help_message'])

@dp.message_handler(state=States.processing)
async def error_processing_handler(message: types.Message, state: FSMContext):
    # Send message
    await message.answer(config['processing_message'])

if __name__ == '__main__':
    print('Start polling...')
    executor.start_polling(dp)
