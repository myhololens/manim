# !/usr/bin/env python3

import sys
# import imp
import importlib
import inspect
import pyclbr
import itertools as it
import os
import subprocess as sp
import traceback

import constants

from scene.scene import Scene
from utils.sounds import play_error_sound
from utils.sounds import play_finish_sound


def handle_scene(scene, **config):
    import platform
    if config["quiet"]:
        curr_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    if config["show_last_frame"]:
        scene.save_image(mode=config["saved_image_mode"])
    open_file = any([
        config["show_last_frame"],
        config["open_video_upon_completion"],
        config["show_file_in_finder"]
    ])
    if open_file:
        commands = ["open"]
        if (platform.system() == "Linux"):
            commands = ["xdg-open"]
        elif (platform.system() == "Windows"):
            commands = ["start"]

        if config["show_file_in_finder"]:
            commands.append("-R")

        if config["show_last_frame"]:
            commands.append(scene.get_image_file_path())
        else:
            commands.append(scene.get_movie_file_path())
        # commands.append("-g")
        FNULL = open(os.devnull, 'w')
        sp.Popen(commands, stdout=FNULL, stderr=sp.STDOUT)
        FNULL.close()

    if config["quiet"]:
        sys.stdout.close()
        sys.stdout = curr_stdout


def is_scene(obj):
    if not inspect.isclass(obj):
        return False
    if not issubclass(obj, Scene):
        return False
    if obj == Scene:
        return False
    return True


def is_child_scene(obj, module):
    if not inspect.isclass(obj):
        return False
    if not issubclass(obj, Scene):
        return False
    if obj == Scene:
        return False
    if not obj.__module__.startswith(module.__name__):
        return False
    return True


def prompt_user_for_choice(name_to_obj):
    num_to_name = {}
    names = sorted(name_to_obj.keys(), key=lambda k: name_to_obj[k].lineno)
    for count, name in zip(it.count(1), names):
        print("%d: %s" % (count, name))
        num_to_name[count] = name
    try:
        user_input = input(constants.CHOOSE_NUMBER_MESSAGE)
        if "-" in user_input:
            start, end = user_input.split("-")
            return [
                num_to_name[num]
                for num in range(int(start), int(end) + 1)
            ]
        else:
            return [
                num_to_name[int(num_str)]
                for num_str in user_input.split(",")
            ]
    except:
        print(constants.INVALID_NUMBER_MESSAGE)
        sys.exit()


def get_scene_classes(scene_names_to_classes, config):
    if len(scene_names_to_classes) == 0:
        print(constants.NO_SCENE_MESSAGE)
        return []
    if len(scene_names_to_classes) == 1:
        return list(scene_names_to_classes.keys())
    if config["scene_name"] in scene_names_to_classes:
        return [config["scene_name"]]
    if config["scene_name"] != "":
        print(constants.SCENE_NOT_FOUND_MESSAGE)
        return []
    if config["write_all"]:
        return list(scene_names_to_classes.keys())
    return prompt_user_for_choice(scene_names_to_classes)


def get_module(file_name):
    sys.path.insert(0, os.path.dirname(file_name))
    module_name = os.path.basename(file_name).replace(".py", "")
    return importlib.import_module(module_name)


def main(config):
    constants.init_directories(config)
    script_module = get_module(config["file"])
    pyclbr_module = pyclbr.readmodule(script_module.__name__)
    scene_names_to_pyclbr_classes = {
        name: pyclbr_class for name, pyclbr_class in pyclbr_module.items()
        if pyclbr_class.module == script_module.__name__
    }
    scene_names_to_classes = dict(
        inspect.getmembers(
            script_module,
            lambda x: inspect.isclass(x) and
            x.__name__ in scene_names_to_pyclbr_classes.keys(),
        )
    )

    # config["output_directory"] = os.path.join(
    #     VIDEO_DIR,
    #     config["file"].replace(".py", "")
    # )

    scene_kwargs = dict([
        (key, config[key])
        for key in [
            "camera_config",
            "frame_duration",
            "skip_animations",
            "write_to_movie",
            "save_pngs",
            "movie_file_extension",
            "start_at_animation_number",
            "end_at_animation_number",
        ]
    ])

    scene_kwargs["name"] = config["output_name"]
    if config["save_pngs"]:
        print("We are going to save a PNG sequence as well...")
        scene_kwargs["save_pngs"] = True
        scene_kwargs["pngs_mode"] = config["saved_image_mode"]

    exit_codes = []
    for scene_name in get_scene_classes(scene_names_to_pyclbr_classes, config):
        try:
            SceneClass = scene_names_to_classes[scene_name]
            handle_scene(SceneClass(**scene_kwargs), **config)
            exit_codes.append(play_finish_sound())
        except:
            print("\n\n")
            traceback.print_exc()
            print("\n\n")
            exit_codes.append(play_error_sound())
    if any(exit_codes):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
