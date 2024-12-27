import pygame as pg
import os
import json
import pathlib

pg.init()
screen = pg.display.set_mode((1, 1))

compression = 2
world_angle = 45
train_sprites = {}
print("Alphen's Isometric Subway Simulator spritestack render dumping program")
train_folder = input("Enter name of folder with train pack to get renders of>")
current_dir = pathlib.Path(__file__).parent.resolve()

folder_contents = os.listdir(os.path.join(current_dir,"paks",train_folder))
if "pack.json" in folder_contents:
    print("Located json file in specified folder!")
    with open(os.path.join(current_dir,"paks",train_folder,"pack.json")) as file:
        pack_parameters = json.loads(file.read())

        if "trains" in pack_parameters:
            for train in pack_parameters["trains"]:
                
                train_parameters = train
                key = train_parameters["system_name"]
                sprite_stack_factor = 4
                
                base_train_sprite = pg.image.load(os.path.join(*([current_dir,"paks",train_folder,train_parameters["sprite"]]))).convert_alpha()

                for sprite_params in train_parameters["sprite_info"]:
                    if sprite_params["type"] == "closed":
                        base_layers = []

                        for j in range(sprite_params["layers"]):
                            x_pos = sprite_params["w"]*j# if not ("reversed" in sprite_params and sprite_params["reversed"]) else sprite_params["h_layer"]*(sprite_params["layer_amount"]-1-i)
                            base_layers.append(pg.transform.scale(base_train_sprite.subsurface(x_pos,sprite_params["y"],sprite_params["w"],sprite_params["h"]),(sprite_params["w"]*4,sprite_params["h"]*4)))


                        for rotation in range(world_angle,world_angle+90*4,90):
                            w, h = pg.transform.rotate(base_layers[0],rotation).get_size()
                            h/=compression
                            rotation = rotation%360

                            surface = pg.Surface((w,h+sprite_params["layers"]*sprite_stack_factor-1))

                            for i in range(sprite_params["layers"]*sprite_stack_factor):
                                pos = (0,surface.get_height()-i-h)
                                base_thingy = pg.transform.rotate(base_layers[int(i/sprite_stack_factor)],rotation)
                                surface.blit(pg.transform.scale(base_thingy,(base_thingy.get_width(),base_thingy.get_height()/compression)),pos)
                            pg.image.save(surface,os.path.join(current_dir,"renders",f"{key}_{rotation}.png"))
else:
    print("Pack not found! Check the spelling of pack name or its integrity.")

pg.quit()