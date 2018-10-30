#!/usr/bin/python3

<<<<<<< HEAD
import extract_scene
extract_scene.main()

# import sys
# import argparse
# # import imp
# import importlib
# import inspect
# import itertools as it
# import os
# import subprocess as sp
# import traceback
# 
# from constants import *
# 
# from scene.scene import Scene
# from utils.sounds import play_error_sound
# from utils.sounds import play_finish_sound
# 
# from colour import Color
# 
# 
# class Manim():
# 
#     def __init__(self):
#         self.config = {
#             "file": "example_file.py",
#             "scene_name": "LiveStream",
#             "open_video_upon_completion": False,
#             "show_file_in_finder": False,
#             # By default, write to file
#             "write_to_movie": True,
#             "show_last_frame": False,
#             "save_pngs": False,
#             # If -t is passed in (for transparent), this will be RGBA
#             "saved_image_mode": "RGB",
#             "movie_file_extension": ".mp4",
#             "quiet": True,
#             "ignore_waits": False,
#             "write_all": False,
#             "name": "LiveStream",
#             "start_at_animation_number": 0,
#             "end_at_animation_number": None,
#             "skip_animations": False,
#             "camera_config": HIGH_QUALITY_CAMERA_CONFIG,
#             "frame_duration": PRODUCTION_QUALITY_FRAME_DURATION,
#         }
=======
=======
>>>>>>> Return a Scene object from the creation of a Manim instance
from constants import *
from scene.scene import Scene


class Manim():

    def __new__(cls):
        kwargs = {
            "scene_name": LIVE_STREAM_NAME,
            "open_video_upon_completion": False,
            "show_file_in_finder": False,
            # By default, write to file
            "write_to_movie": True,
            "show_last_frame": False,
            "save_pngs": False,
            # If -t is passed in (for transparent), this will be RGBA
            "saved_image_mode": "RGB",
            "movie_file_extension": ".mp4",
            "quiet": True,
            "ignore_waits": False,
            "write_all": False,
            "name": LIVE_STREAM_NAME,
            "start_at_animation_number": 0,
            "end_at_animation_number": None,
            "skip_animations": False,
            "camera_config": HIGH_QUALITY_CAMERA_CONFIG,
            "frame_duration": PRODUCTION_QUALITY_FRAME_DURATION,
            "is_live_streaming": IS_LIVE_STREAMING
        }
<<<<<<< HEAD
>>>>>>> Add is_live_streaming control flow to idle the scene generation pipe for interactive shell usage purpose
=======
        return Scene(**kwargs)
>>>>>>> Return a Scene object from the creation of a Manim instance
