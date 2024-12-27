import pygame as pg
import os
import json
import math
import time
import threading
import random
import pathlib
import pprint
from res.train import *

version = "0.6 Е-обноволение"
version_id = version.split(" ")[0]
changelog = [
    "v0.6 'E-type update'",
    "-added type 'E' 81-703 EMU"
]
scale = 1
CURRENT_DIRECTORY = ""
current_dir = CURRENT_DIRECTORY
#directory deprecated 11-11-24 to work with cxFreeze and be able to use non-packed gamedata

#from train import *
#Train module deprecated and merged with main 11-11-24
#ага, напиздел. вернул обратно, но теперь оно живёт в res/. 24-11-24 

player_pos = [0,0]
block_pos = [0,0]
block_size = (256,1024)
working = True
controlling = -1
controlling_consist = None
following = -1
debug = 0
world_angle = 45
compression = 2
volume = 0
hotkeys = {"vz_1":pg.K_n,"rp_return":pg.K_b,"left_doors":pg.K_a,"right_doors":pg.K_d,"close_doors":pg.K_v}
text_color = (200,200,200)
text_black = (25,25,25)

main_font_height = 20
title_font_height = 30

pg.init()
clock = pg.time.Clock()
screen = pg.display.set_mode((0, 0), pg.FULLSCREEN, pg.SRCALPHA)
title_font = pg.font.Font(os.path.join(CURRENT_DIRECTORY,"res","verdana.ttf"),title_font_height)
font = pg.font.Font(os.path.join(CURRENT_DIRECTORY,"res","verdana.ttf"),main_font_height)
annotation_font = pg.font.Font(os.path.join(CURRENT_DIRECTORY,"res","verdana.ttf"),12)
temp_text = font.render("abcdefghijklmnopqrtsuvwxyz",True,(0,0,0))
char_width = temp_text.get_width()/26

screen_size = screen.get_size()
#screen = pg.display.set_mode(screen_size, pg.SRCALPHA)
pg.display.set_caption(f"Alphen's Isometric Subway Simulator v{version_id}")
screen_state = "loading"

sprite_loading_info = []
ground_sprites = {}
train_sprites = {}
train_repaint_dictionary = {}
icons = {}
train_types = {}
misc_sprites = {}
sounds = {}
consists_info = {}
consists = {}

sdk_params = {
    "folder_list":[],
    "folder_pointer":-1,
    "consist_pointer":-1,
    "scale":4,
    "editing":False
}
sdk_loaded_pack = {"graphics":{},"info":{}}

progress = 0
load_timer = 0
current_tool = -1
current_toolbar = 0
custom_tool_parameters = ["","",0]
spawn_menu = [False, 0, None, None]
toolbar = [["tstr","tca1","tca2","tcb1","tcb2","tsa1","tsa2","tsb1","tsb2","custom_tile"]]

pg.mixer.init()
channel_rolling = pg.mixer.Channel(1)
channel_rolling.set_volume(0.125)

sign = lambda x: math.copysign(1, x)

def text_splitter(base_string, char_width,max_width):
    max_char_per_line = int(max_width/char_width)
    return [base_string[i:i+max_char_per_line] for i in range(0, len(base_string), max_char_per_line)]

def sprite_load_routine():
    global ground_sprites, train_sprites,train_types, sounds, consists_info,CURRENT_DIRECTORY,sprite_loading_info,screen_state,consists,progress,icons,train_repaint_dictionary, load_timer, misc_sprites
    pak_folders = os.listdir(os.path.join(current_dir,"paks"))
    train_sprites["sprites"] = {}
    train_sprites["controls"] = {}

    for folder in pak_folders:
        folder_contents = os.listdir(os.path.join(current_dir,"paks",folder))
        if "pack.json" in folder_contents:
            
            with open(os.path.join(CURRENT_DIRECTORY,"paks",folder,"pack.json"),encoding="utf-8") as file:
                pack_parameters = json.loads(file.read())

                temp_sprites = {}
                filenames = os.listdir(os.path.join(CURRENT_DIRECTORY,"paks",folder))
                for filename in filenames:
                    if filename[-4:] == ".png":
                        temp_sprites[filename[:-4]] = pg.image.load(os.path.join(*([CURRENT_DIRECTORY,"paks",folder,filename]))).convert_alpha()

                if "tiles" in pack_parameters:
                    
                    for info_pack in pack_parameters["tiles"]:

                        base_ground_sprite = temp_sprites[info_pack["filename"]].subsurface(info_pack["params"][0],info_pack["params"][1],info_pack["params"][2]*info_pack["params"][4],info_pack["params"][3])

                        base_layers = []
                        sprite_stack_factor = 4
                        
                        for i in range(info_pack["params"][4]):
                            x_pos = info_pack["params"][2]*i# if not ("reversed" in sprite_params and sprite_params["reversed"]) else sprite_params["h_layer"]*(sprite_params["layer_amount"]-1-i)
                            base_layers.append(pg.transform.flip(pg.transform.scale(base_ground_sprite.subsurface(x_pos,0,info_pack["params"][2],info_pack["params"][3]),(info_pack["params"][2]*4,info_pack["params"][3]*4)),info_pack["params"][6],info_pack["params"][7]))

                        ground_sprites[info_pack["name"]] = {}

                        for rotation in [world_angle]:
                            w, h = pg.transform.rotate(base_layers[0],rotation).get_size()
                            h=h/compression

                            surface = pg.Surface((w,h+(info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor))
                            surface.set_colorkey((0,0,0))

                            for i in range(info_pack["params"][4]*sprite_stack_factor):
                                pos = (0,surface.get_height()-i-h-info_pack["params"][5]*sprite_stack_factor)
                                base_img = pg.transform.rotate(base_layers[int(i/sprite_stack_factor)],rotation)
                                surface.blit(pg.transform.scale(base_img,(base_img.get_width(),base_img.get_height()/compression)),pos)
                            ground_sprites[info_pack["name"]][rotation] = surface
                            progress+=1
                        for q in range(4):
                            w, h = pg.transform.rotate(base_layers[0].subsurface(0,base_layers[0].get_height()/4*q,base_layers[0].get_width(),base_layers[0].get_height()/4),rotation).get_size()
                            h=h/compression

                            surface = pg.Surface((w,h+(info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor))
                            surface.set_colorkey((0,0,0))

                            for i in range(info_pack["params"][4]*sprite_stack_factor):
                                pos = (0,surface.get_height()-i-h-info_pack["params"][5]*sprite_stack_factor)
                                z=base_layers[int(i/sprite_stack_factor)]
                                base_img = pg.transform.rotate(z.subsurface(0,z.get_height()/4*q,z.get_width(),z.get_height()/4),rotation)
                                surface.blit(pg.transform.scale(base_img,(base_img.get_width(),base_img.get_height()/compression)),pos)
                            ground_sprites[info_pack["name"]][q] = surface
                            progress+=1
                        ground_sprites[info_pack["name"]]["height"] = (info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor-1
                
                if "misc" in pack_parameters:
                    for misc_sprite_param in pack_parameters["misc"]:
                        misc_sprites[misc_sprite_param["name"]] = pg.transform.flip(
                            temp_sprites[misc_sprite_param["filename"]].subsurface(
                                misc_sprite_param["params"][0],misc_sprite_param["params"][1],
                                misc_sprite_param["params"][2],misc_sprite_param["params"][3]),
                            misc_sprite_param["params"][4],misc_sprite_param["params"][5])

                if "icons" in pack_parameters:
                    for icon_param in pack_parameters["icons"]:
                        icons[icon_param["name"]] = pg.transform.flip(
                            temp_sprites["icons"].subsurface(icon_param["params"][0],icon_param["params"][1],icon_param["params"][2],icon_param["params"][3]),
                            icon_param["params"][4],icon_param["params"][5])


                if "consists" in pack_parameters:
                    for train in pack_parameters["consists"]:
                        train_parameters = train
                        base_control_panel_sprite = pg.image.load(os.path.join(*([current_dir,"paks",folder,train_parameters["control_panel_sprite"]]))).convert_alpha()
                        key = train_parameters["system_name"]
                        train_sprites["controls"][key] = {}
                        train_repaint_dictionary[key] = []
                        consists_info[key] = train_parameters["traction_info"]
                        sprite_stack_factor = 4

                        controls_info = train_parameters["control_panel_info"]
                        for control in controls_info:
                            train_sprites["controls"][key][control] = pg.transform.scale(
                                base_control_panel_sprite.subsurface(controls_info[control]["x"],controls_info[control]["y"],controls_info[control]["w"],controls_info[control]["h"]),
                                (controls_info[control]["w"]*controls_info[control]["scale"],controls_info[control]["h"]*controls_info[control]["scale"]))

                        train_types[key] = {}
                        train_types[key]["size"] = train_parameters["clickable_size"]
                        train_types[key]["name"] = train_parameters["name"]

                        sounds[key] = {}
                        for sound in train_parameters["sound_loading_info"]:
                            sounds[key][sound] = pg.mixer.Sound(os.path.join(CURRENT_DIRECTORY,"paks",folder,train_parameters["sound_loading_info"][sound]))
                            sounds[key][sound].set_volume(volume)
                if "trains" in pack_parameters:
                    for train in pack_parameters["trains"]:
                        
                        train_parameters = train
                        key = train_parameters["system_name"]
                        train_sprites["sprites"][key] = {}
                        train_repaint_dictionary[train_parameters["designed_for"]].append(key)
                        train_sprites["sprites"][key]["name"] = train_parameters["name"]
                        sprite_stack_factor = 4
                        
                        base_train_sprite = pg.image.load(os.path.join(*([current_dir,"paks",folder,train_parameters["sprite"]]))).convert_alpha()

                        for sprite_params in train_parameters["sprite_info"]:
                            base_layers = []
                            door_type = sprite_params["type"]
                            train_sprites["sprites"][key][door_type] = {"type":door_type}

                            for j in range(sprite_params["layers"]):
                                x_pos = sprite_params["w"]*j# if not ("reversed" in sprite_params and sprite_params["reversed"]) else sprite_params["h_layer"]*(sprite_params["layer_amount"]-1-i)
                                base_layers.append(pg.transform.scale(base_train_sprite.subsurface(x_pos,sprite_params["y"],sprite_params["w"],sprite_params["h"]),(sprite_params["w"]*4,sprite_params["h"]*4)))


                            for rotation in [0,180,world_angle,world_angle+180]+[8.25+world_angle,14+world_angle,-8.25+world_angle,-14+world_angle,180-8.25+world_angle,180-14+world_angle,180+8.25+world_angle,180+14+world_angle]:
                                w, h = pg.transform.rotate(base_layers[0],rotation).get_size()
                                h/=compression
                                rotation = rotation%360

                                global_l_surface = pg.Surface((w,h+sprite_params["layers"]*sprite_stack_factor-1))
                                global_r_surface = pg.Surface((w,h+sprite_params["layers"]*sprite_stack_factor-1))
                                global_l_surface.set_colorkey((0,0,0))
                                global_r_surface.set_colorkey((0,0,0))

                                for i in range(sprite_params["layers"]*sprite_stack_factor):
                                    pos = (0,global_l_surface.get_height()-i-h)
                                    surf_size = base_layers[int(i/sprite_stack_factor)].get_size()
                                    l_surface = pg.Surface(size=surf_size,masks=None)
                                    r_surface = pg.Surface(size=surf_size,masks=None)
                                    l_surface.set_colorkey((0,0,0))
                                    r_surface.set_colorkey((0,0,0))

                                    l_surface.blit(base_layers[int(i/sprite_stack_factor)].subsurface(
                                        0,
                                        0,
                                        base_layers[int(i/sprite_stack_factor)].get_width()/2,
                                        base_layers[int(i/sprite_stack_factor)].get_height()
                                    ),(0,0))
                                    r_surface.blit(base_layers[int(i/sprite_stack_factor)].subsurface(
                                        base_layers[int(i/sprite_stack_factor)].get_width()/2,
                                        0,
                                        base_layers[int(i/sprite_stack_factor)].get_width()/2,
                                        base_layers[int(i/sprite_stack_factor)].get_height()
                                    ),(base_layers[int(i/sprite_stack_factor)].get_width()/2,0))
                                    l_surface = pg.transform.rotate(l_surface,rotation)
                                    r_surface = pg.transform.rotate(r_surface,rotation)
                                    l_surface.set_colorkey((0,0,0))
                                    r_surface.set_colorkey((0,0,0))
                                    global_l_surface.blit(pg.transform.scale(l_surface,(l_surface.get_width(),l_surface.get_height()/compression)),pos)
                                    global_r_surface.blit(pg.transform.scale(r_surface,(r_surface.get_width(),r_surface.get_height()/compression)),pos)
                                train_sprites["sprites"][key][door_type][rotation] = {}
                                train_sprites["sprites"][key][door_type][rotation]["l"] = global_l_surface
                                train_sprites["sprites"][key][door_type][rotation]["r"] = global_r_surface

                            train_sprites["sprites"][key][door_type]["height"] = sprite_params["layers"]*sprite_stack_factor-1
        progress+=1

    screen_state = "title"
    load_timer = 200
    consists = {}
'''
world = {
    (0,17):["tstr"],
    (0,16):["tsb1"],(-1,16):["tcb2"],
    (1,15):["stroitelnaya_platform_f","stroitelnaya_walls_f"],(0,15):["stroitelnaya_track_f_tstr"],(-1,15):["stroitelnaya_track_tstr"],(-2,15):["stroitelnaya_platform","stroitelnaya_walls"],
    (0,14):["tstr"],(-1,14):["tstr"],
    (0,13):["tstr"],(-1,13):["tstr"],
    (1,12):["tca2"],(0,12):["tca1"],(-1,12):["tcb1"],(-2,12):["tcb2"],
    (1,11):["tstr"],(-2,11):["tstr"],
    (1,10):["tstr"],(-2,10):["tstr"],
    (1,9):["tsb1"],(0,9):["tcb2"],(-2,9):["tstr"],
    (1,8):["tstr"],(0,8):["tcb1"],(-1,8):["tcb2"],(-2,8):["tstr"],
    (1,7):["tstr"],(-1,7):["tcb1"],(-2,7):["tsb2"],
    (1,6):["vokzalnaya_track_tstr"],(0,6):["vokzalnaya_platform","vokzalnaya_walls"],(-1,6):["vokzalnaya_platform_f","vokzalnaya_walls_f"],(-2,6):["vokzalnaya_track_f_tstr"],
    (1,5):["tstr"],(-2,5):["tstr"],
    (1,4):["tstr"],(-2,4):["tstr"],
    (1,3):["tstr"],(-2,3):["tstr"],
    (1,2):["tstr"],(-2,2):["tstr"],
    (1,1):["tstr"],(-2,1):["tstr"],
    (1,0):["sterlitamakskaya_track_tstr"],(0,0):["sterlitamakskaya_platform","sterlitamakskaya_walls"],(-1,0):["sterlitamakskaya_platform_f","sterlitamakskaya_walls_f"],(-2,0):["sterlitamakskaya_track_f_tstr"],
    (1,-1):["tstr"],(-2,-1):["tstr"],
    (1,-2):["tstr"],(-2,-2):["tstr"],
    (1,-3):["tstr"],(-2,-3):["tstr"],
    (1,-4):["tstr"],(-2,-4):["tstr"],
    (1,-5):["tstr"],(-2,-5):["tstr"],
    (1,-6):["kochetova_track_tstr"],(0,-6):["kochetova_platform","kochetova_walls"],(-1,-6):["kochetova_platform_f","kochetova_walls_f"],(-2,-6):["kochetova_track_f_tstr"],
    (1,-7):["tstr"],(-2,-7):["tstr"],
    (1,-8):["tstr"],(-2,-8):["tstr"],
    (1,-9):["tstr"],(-2,-9):["tstr"],
    (1,-10):["tstr"],(-2,-10):["tstr"],
    (1,-11):["tstr"],(-2,-11):["tstr"],
    (1,-12):["sodovaya_track_tstr"],(0,-12):["sodovaya_platform","sodovaya_walls"],(-1,-12):["sodovaya_platform_f","sodovaya_walls_f"],(-2,-12):["sodovaya_track_f_tstr"],
    (1,-13):["tcb1"],(0,-13):["tcb2"],(-1,-13):["tca2"],(-2,-13):["tca1"],
    (0,-14):["tstr"],(-1,-14):["tstr"],
    (0,-15):["tsa2"],(-1,-15):["tsa1"],
    (0,-16):["tstr"],(-1,-16):["tstr"]}
'''
world = {(-6, 26): ['tca1'],
 (-6, 27): ['tstr'],
 (-6, 28): ['sovetskaya_track_f_tstr', ''],
 (-6, 29): ['tstr'],
 (-6, 30): ['tcb2'],
 (-5, 25): ['tca1'],
 (-5, 26): ['tca2'],
 (-5, 28): ['sovetskaya_platform_f', 'sovetskaya_walls_f'],
 (-5, 30): ['tcb1'],
 (-5, 31): ['tcb2'],
 (-4, 18): ['tca1'],
 (-4, 19): ['tstr'],
 (-4, 20): ['vokzalnaya_track_f_tstr', ''],
 (-4, 21): ['tsb2'],
 (-4, 22): ['tstr'],
 (-4, 23): ['tstr'],
 (-4, 24): ['tstr'],
 (-4, 25): ['tca2'],
 (-4, 28): ['sovetskaya_platform', 'sovetskaya_walls'],
 (-4, 31): ['tcb1'],
 (-4, 32): ['tcb2'],
 (-3, 17): ['tca1'],
 (-3, 18): ['tca2'],
 (-3, 20): ['vokzalnaya_platform_f', 'vokzalnaya_walls_f'],
 (-3, 21): ['tcb1'],
 (-3, 22): ['tcb2'],
 (-3, 26): ['tca1'],
 (-3, 27): ['tstr'],
 (-3, 28): ['sovetskaya_track_tstr', ''],
 (-3, 29): ['tstr'],
 (-3, 30): ['tcb2'],
 (-3, 32): ['tcb1'],
 (-3, 33): ['tstr'],
 (-3, 34): ['sterlitamakskaya_track_f_tstr', ''],
 (-3, 35): ['tsb2'],
 (-3, 36): ['tstr'],
 (-3, 37): ['tstr'],
 (-2, 16): ['tca1'],
 (-2, 17): ['tca2'],
 (-2, 20): ['vokzalnaya_platform', 'vokzalnaya_walls'],
 (-2, 22): ['tcb1'],
 (-2, 23): ['tcb2'],
 (-2, 25): ['tca1'],
 (-2, 26): ['tca2'],
 (-2, 30): ['tcb1'],
 (-2, 31): ['tcb2'],
 (-2, 34): ['sterlitamakskaya_platform_f', 'sterlitamakskaya_walls_f'],
 (-2, 35): ['tcb1'],
 (-2, 36): ['tsa1'],
 (-2, 37): ['tstr'],
 (-1, -3): ['tstr'],
 (-1, -2): ['tstr'],
 (-1, -1): ['tstr'],
 (-1, 0): ['tstr'],
 (-1, 1): ['tsa1'],
 (-1, 2): ['tstr'],
 (-1, 3): ['sodovaya_track_f_tstr', ''],
 (-1, 4): ['tstr'],
 (-1, 5): ['tstr'],
 (-1, 6): ['tstr'],
 (-1, 7): ['tstr'],
 (-1, 8): ['tstr'],
 (-1, 9): ['kochetova_track_f_tstr', ''],
 (-1, 10): ['tstr'],
 (-1, 11): ['tstr'],
 (-1, 12): ['tstr'],
 (-1, 13): ['tstr'],
 (-1, 14): ['park_kultury_track_f_tstr', ''],
 (-1, 15): ['tstr'],
 (-1, 16): ['tca2'],
 (-1, 18): ['tca1'],
 (-1, 19): ['tstr'],
 (-1, 20): ['vokzalnaya_track_tstr', ''],
 (-1, 21): ['tstr'],
 (-1, 22): ['tstr'],
 (-1, 23): ['tsb1'],
 (-1, 24): ['tstr'],
 (-1, 25): ['tca2'],
 (-1, 31): ['tcb1'],
 (-1, 32): ['tcb2'],
 (-1, 34): ['sterlitamakskaya_platform', 'sterlitamakskaya_walls'],
 (-1, 35): ['tca1'],
 (-1, 36): ['tca2'],
 (0, 0): ['tca1'],
 (0, 1): ['tca2'],
 (0, 3): ['sodovaya_platform_f', 'sodovaya_walls_f'],
 (0, 9): ['kochetova_platform_f', 'kochetova_walls_f'],
 (0, 14): ['park_kultury_platform_f', 'park_kultury_walls_f'],
 (0, 17): ['tca1'],
 (0, 18): ['tca2'],
 (0, 32): ['tcb1'],
 (0, 33): ['tstr'],
 (0, 34): ['sterlitamakskaya_track_tstr', ''],
 (0, 35): ['tsa2'],
 (0, 36): ['tstr'],
 (0, 37): ['tstr'],
 (1, -1): ['tca1'],
 (1, 0): ['tca2'],
 (1, 3): ['sodovaya_platform', 'sodovaya_walls'],
 (1, 9): ['kochetova_platform', 'kochetova_walls'],
 (1, 14): ['park_kultury_platform', 'park_kultury_walls'],
 (1, 16): ['tca1'],
 (1, 17): ['tca2'],
 (2, -3): ['tstr'],
 (2, -2): ['tstr'],
 (2, -1): ['tsa2'],
 (2, 0): ['tstr'],
 (2, 1): ['tstr'],
 (2, 2): ['tstr'],
 (2, 3): ['sodovaya_track_tstr', ''],
 (2, 4): ['tstr'],
 (2, 5): ['tstr'],
 (2, 6): ['tstr'],
 (2, 7): ['tstr'],
 (2, 8): ['tstr'],
 (2, 9): ['kochetova_track_tstr', ''],
 (2, 10): ['tstr'],
 (2, 11): ['tstr'],
 (2, 12): ['tstr'],
 (2, 13): ['tstr'],
 (2, 14): ['park_kultury_track_tstr', ''],
 (2, 15): ['tstr'],
 (2, 16): ['tca2']}
switches = {(-4, 21): False,
 (-3, 35): False,
 (-2, 36): False,
 (-1, 1): False,
 (-1, 23): False,
 (0, 35): False,
 (2, -1): False}

#trains = {}

player_pos = [256*0.5,1024*0.5]
m_btn = [0,0,0]
world_mouse_coord = [0,0]
mouse_block_pos = (None,None)
mouse_clicked = False
mouse_released = False
line_pos = 0

sprite_thread = threading.Thread(target=sprite_load_routine,daemon=True) #,args=[world]
sprite_thread.start()

while working:
    tunnel_nothingness = (15,15,15)
    keydowns = []
    keyups = []
    mouse_clicked_prev = mouse_clicked
    mouse_clicked = False
    mouse_released = False
    for evt in pg.event.get():
        if evt.type == pg.QUIT:
            working = False
        if evt.type == pg.KEYDOWN:
            keydowns.append(evt.key)
            if evt.key == pg.K_q and screen_state == "playing":
                debug = (debug+1)%3
            
            if screen_state == "editor" and custom_tool_parameters[2] != 0:
                if evt.key == pg.K_BACKSPACE:
                    custom_tool_parameters[custom_tool_parameters[2]-1] = custom_tool_parameters[custom_tool_parameters[2]-1][:-1]
                else:
                    custom_tool_parameters[custom_tool_parameters[2]-1] += evt.unicode
            if screen_state == "sdk" and sdk_params["editing"]:
                element_name = list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys())[sdk_params["element_pointer"]]
                element_name_new = element_name
                if evt.key == pg.K_BACKSPACE:
                    element_name_new=element_name[:-1]
                elif evt.key == pg.K_RETURN:
                    sdk_params["editing"] = False
                else:
                    element_name_new += evt.unicode
                
                tmp = sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][element_name]
                sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].pop(element_name)
                sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][element_name_new] = tmp
                sdk_params["element_pointer"] = list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys()).index(element_name_new)
        if evt.type == pg.KEYUP:
            keyups.append(evt.key)
        if evt.type == pg.MOUSEBUTTONDOWN and not m_btn[0] and not m_btn[2]:
            mouse_clicked = True
        elif evt.type == pg.MOUSEBUTTONUP:
            mouse_released = True
    if screen_state == "loading":
        text_color = (200,200,200)
        screen.fill(tunnel_nothingness)
        text = font.render("загрузка...", True, text_color)
        screen.blit(text,(screen_size[0]/2-text.get_width()/2, screen_size[1]/2-text.get_height()))
        line_pos = (line_pos + 2) % 280
        thingy_color = (128,255,0) if sprite_thread.is_alive() else (204,20,20)
        pg.draw.rect(screen,thingy_color,((screen_size[0]/2-124+line_pos) if 0 < line_pos < 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
        pg.draw.rect(screen,thingy_color,((screen_size[0]/2-124+line_pos-6) if 0 < line_pos-6< 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
        pg.draw.rect(screen,thingy_color,((screen_size[0]/2-124+line_pos-12) if 0 < line_pos-12 < 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
        pg.draw.rect(screen,(255,255,255),(screen_size[0]/2-124,screen_size[1]/2+2,248,text.get_height()-4),2)

    elif screen_state == "title":
        pressed = pg.key.get_pressed()
        m_pos = pg.mouse.get_pos()
        m_btn = pg.mouse.get_pressed()
        
        text_color = (200,200,200)
        screen.fill(tunnel_nothingness)
        #text = font.render(f"Alphen's Isometric Subway Simulator v{version_id}", True, text_color)
        #screen.blit(text,(screen_size[0]/2-text.get_width()/2, screen_size[1]/2-2*text.get_height()))
        
        screen.blit(
            pg.transform.scale(
                misc_sprites["game_icon"],(
                misc_sprites["game_icon"].get_width(),
                misc_sprites["game_icon"].get_height()
            )),(
                36,
                36
            ))
        text = font.render("alphen's isometric", True, text_black)
        screen.blit(text,(36+128+20,36+64-text.get_height()-2))
        text = font.render("subway simulator", True, text_black)
        screen.blit(text,(36+128+20,36+64+2))

        text_lines = [
            [font.render("Start a new game",True,text_color),"playing"],
            None,
            [font.render("Map editor",True,text_color),"editor"],
            [font.render("Pack editor",True,text_color),"sdk_load"],
            None,
            [font.render("Options",True,text_color),None],
            None,
            [font.render("Quit",True,text_color),"exit"]
        ]

        for i,line in enumerate(text_lines):
            if line != None:
                screen.blit(line[0],(64,36+128+20+(main_font_height+4)*i))
                if line[1] != None and m_btn[0] and load_timer <= 200:
                    if (64 <= m_pos[0] <= 64+line[0].get_width() and 
                    36+128+20+(main_font_height+4)*i <= m_pos[1] <= 36+128+20+(main_font_height+4)*(i+1)):
                        player_pos = [0,0]
                        screen_state = line[1]

        if load_timer > 0:
            loadscreen_surf = pg.Surface(screen_size)
            text_color = (200,200,200)
            loadscreen_surf.fill(tunnel_nothingness)
            text = font.render("загрузка...", True, text_color)
            loadscreen_surf.blit(text,(screen_size[0]/2-text.get_width()/2, screen_size[1]/2-text.get_height()))
            line_pos = (line_pos + 2) % 280
            pg.draw.rect(loadscreen_surf,(128,255,0),((screen_size[0]/2-124+line_pos) if 0 < line_pos < 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
            pg.draw.rect(loadscreen_surf,(128,255,0),((screen_size[0]/2-124+line_pos-6) if 0 < line_pos-6< 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
            pg.draw.rect(loadscreen_surf,(128,255,0),((screen_size[0]/2-124+line_pos-12) if 0 < line_pos-12 < 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
            pg.draw.rect(loadscreen_surf,(255,255,255),(screen_size[0]/2-124,screen_size[1]/2+2,248,text.get_height()-4),2)
            loadscreen_surf.convert()
            loadscreen_surf.set_alpha(255*(load_timer/200))
            screen.blit(loadscreen_surf,(0,0))
            load_timer -= 2

            
    elif screen_state == "sdk":
        old_m_pos = m_pos
        screen.fill(tunnel_nothingness)
        div = 4
        
        pressed = pg.key.get_pressed()
        m_pos = pg.mouse.get_pos()
        m_btn = pg.mouse.get_pressed()

        temp_text = font.render("abcdefghijklmnopqrtsuvwxyz",True,(0,0,0))
        char_width = temp_text.get_width()/26
        text_height = 20
        text_delta = 26
        base_left_pos = screen_size[0]/div*(div-1)

        folder_height = 20
        consist_height = folder_height+text_delta*len(["Select a folder" if sdk_params["folder_pointer"] == -1 else sdk_params["folder_list"][sdk_params["folder_pointer"]]])+30+15
        element_height = consist_height+text_delta*len(["Select a consist" if sdk_params["consist_pointer"] == -1 else sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["name"]])+30+15

        if "panel" in sdk_loaded_pack["graphics"]:
            screen.blit(pg.transform.scale(sdk_loaded_pack["graphics"]["panel"],
                    (sdk_loaded_pack["graphics"]["panel"].get_width()*sdk_params["scale"],sdk_loaded_pack["graphics"]["panel"].get_height()*sdk_params["scale"])),
                (screen_size[0]/2-sdk_loaded_pack["graphics"]["panel"].get_width()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][0],
                 screen_size[1]/2-sdk_loaded_pack["graphics"]["panel"].get_height()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][1])
                )
            if sdk_params["element_pointer"] != -1:
                key = list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys())[sdk_params["element_pointer"]]
                param = sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][key]
                tmp_surf = pg.Surface((param["w"]*sdk_params["scale"],param["h"]*sdk_params["scale"]))
                pg.draw.rect(tmp_surf,(240,240,240),(
                    0,
                    0,
                    param["w"]*sdk_params["scale"],
                    param["h"]*sdk_params["scale"]
                ))
                tmp_surf.convert()
                tmp_surf.set_alpha(64)
                screen.blit(tmp_surf,(
                    screen_size[0]/2-sdk_loaded_pack["graphics"]["panel"].get_width()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][0]+param["x"]*sdk_params["scale"],
                    screen_size[1]/2-sdk_loaded_pack["graphics"]["panel"].get_height()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][1]+param["y"]*sdk_params["scale"]))
                pg.draw.rect(screen,(240,240,240),(
                    screen_size[0]/2-sdk_loaded_pack["graphics"]["panel"].get_width()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][0]+param["x"]*sdk_params["scale"],
                    screen_size[1]/2-sdk_loaded_pack["graphics"]["panel"].get_height()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][1]+param["y"]*sdk_params["scale"],
                    param["w"]*sdk_params["scale"],
                    param["h"]*sdk_params["scale"]
                ),2)

        if m_btn[1]:
            sdk_loaded_pack["pos"][0] += m_pos [0] - old_m_pos[0]
            sdk_loaded_pack["pos"][1] += m_pos [1] - old_m_pos[1]

        if (m_btn[0] or m_btn[2]) and mouse_clicked and m_pos[0] < base_left_pos:
            if "panel" in sdk_loaded_pack["graphics"] and sdk_params["element_pointer"] != -1:
                key = list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys())[sdk_params["element_pointer"]]
                param = sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][key]
                x1,y1,x2,y2 = param["x"],param["y"],param["x"]+param["w"],param["y"]+param["h"]
                click_x = int((m_pos[0]-(screen_size[0]/2-sdk_loaded_pack["graphics"]["panel"].get_width()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][0]))/sdk_params["scale"])
                click_y = int((m_pos[1]-(screen_size[1]/2-sdk_loaded_pack["graphics"]["panel"].get_height()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][1]))/sdk_params["scale"])
                if m_btn[0]:
                    if click_x < x2: x1 = click_x
                    elif click_x > x2:
                        x1 = x2
                        x2 = click_x

                    if click_y < y2: y1 = click_y
                    elif click_y > y2:
                        y1 = y2
                        y2  = click_y

                elif m_btn[2]:
                    if click_x > x1: x2 = click_x
                    elif click_x < x1:
                        x2 = x1
                        x1 = click_x

                    if click_y > y1: y2 = click_y
                    elif click_y < y1:
                        y2 = y1
                        y1 = click_y
                sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][key]["x"] = x1
                sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][key]["y"] = y1
                sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][key]["w"] = x2-x1
                sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][key]["h"] = y2-y1


        pg.draw.rect(screen,(200,200,200),(screen_size[0]/div*(div-1),0,screen_size[0]/div+128,screen_size[1]))
        sdk_menu_blocks = [
            [folder_height,"",["Select a folder" if sdk_params["folder_pointer"] == -1 else sdk_params["folder_list"][sdk_params["folder_pointer"]]]],
        ]

        if sdk_loaded_pack["info"] != {}:
            sdk_menu_blocks.append([consist_height,"",["Select a consist" if sdk_params["consist_pointer"] == -1 else sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["name"]]])
        
        if sdk_params["consist_pointer"] != -1:
            sdk_menu_blocks.append([element_height,"",["Select an sprite"] if sdk_params["element_pointer"] == -1 else text_splitter(
                list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys())[sdk_params["element_pointer"]],
                char_width,
                screen_size[0]/div-30
            )])

        for l, z in enumerate(sdk_menu_blocks):
            block_height, block_name, block_set = z
            pg.draw.rect(screen,(128,128,128),
                (base_left_pos+5,
                block_height-5,
                screen_size[0]/div-10,
                text_delta*len(block_set)+40
            ))
            for e, i in enumerate(block_set):
                spawn_menu_text = font.render(i,True,(80,10,10 ) if l == 2 and sdk_params["editing"] else text_black)
                screen.blit(spawn_menu_text, 
                    (base_left_pos+screen_size[0]/div/2-spawn_menu_text.get_width()/2,
                    block_height+text_delta*e
                ))

            is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0]
        
            pg.draw.rect(screen,(15,15,15),
                            (base_left_pos+12,
                            block_height+text_delta*len(block_set)+2,28,28))
            pg.draw.rect(screen,(50,50,50),
                            (base_left_pos+10+2*is_on_button,
                            block_height+text_delta*len(block_set)+2*is_on_button,28,28))
            pg.draw.rect(screen,(100,100,100),
                            (base_left_pos+12+2*is_on_button,
                            block_height+text_delta*len(block_set)+2+2*is_on_button,24,24))
            pg.draw.polygon(screen,text_black,
                            (
                                (base_left_pos+16+2*is_on_button,
                                block_height+text_delta*len(block_set)+14+2*is_on_button),
                                (base_left_pos+10+22+2*is_on_button,
                                block_height+text_delta*len(block_set)+6+2*is_on_button),
                                (base_left_pos+10+22+2*is_on_button,
                                block_height+text_delta*len(block_set)+22+2*is_on_button),
                            ))
            
            if l == 0:
                is_on_button = (base_left_pos+screen_size[0]/div/2-120 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2-10) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0] and sdk_params["folder_pointer"] != -1

                pg.draw.rect(screen,(15,15,15),
                                (base_left_pos+screen_size[0]/div/2-118,
                                block_height+text_delta*len(block_set)+2,108,28))
                pg.draw.rect(screen,(50,50,50),
                                (base_left_pos+screen_size[0]/div/2-120+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,108,28))
                pg.draw.rect(screen,(100,100,100),
                                (base_left_pos+screen_size[0]/div/2-118+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,104,24))
                text = font.render("Load",True,text_black)
                screen.blit(text, (base_left_pos+screen_size[0]/div/2-10-108/2-text.get_width()/2+2*is_on_button, block_height+text_delta*len(block_set)+14+2*is_on_button-text.get_height()/2))

                is_on_button = (base_left_pos+screen_size[0]/div/2+10 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2+120) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0] and sdk_params["folder_pointer"] != -1 and sdk_loaded_pack["info"] != {}

                pg.draw.rect(screen,(15,15,15),
                                (base_left_pos+screen_size[0]/div/2+12,
                                block_height+text_delta*len(block_set)+2,108,28))
                pg.draw.rect(screen,(50,50,50),
                                (base_left_pos+screen_size[0]/div/2+10+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,108,28))
                pg.draw.rect(screen,(100,100,100),
                                (base_left_pos+screen_size[0]/div/2+12+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,104,24))
                text = font.render("Save",True,text_black)
                screen.blit(text, (base_left_pos+screen_size[0]/div/2+12+108/2-text.get_width()/2+2*is_on_button, block_height+text_delta*len(block_set)+14+2*is_on_button-text.get_height()/2))

            if l == 2:
                is_on_button = (base_left_pos+screen_size[0]/div/2-120 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2-120+70) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0]

                pg.draw.rect(screen,(15,15,15),
                                (base_left_pos+screen_size[0]/div/2-118,
                                block_height+text_delta*len(block_set)+2,68,28))
                pg.draw.rect(screen,(50,50,50),
                                (base_left_pos+screen_size[0]/div/2-120+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,68,28))
                pg.draw.rect(screen,(100,100,100),
                                (base_left_pos+screen_size[0]/div/2-118+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,64,24))
                text = font.render("Add",True,text_black)
                screen.blit(text, (base_left_pos+screen_size[0]/div/2-120+68/2-text.get_width()/2+2*is_on_button, block_height+text_delta*len(block_set)+14+2*is_on_button-text.get_height()/2))

                is_on_button = (base_left_pos+screen_size[0]/div/2-40 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2+40) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0] and sdk_params["element_pointer"] != -1

                pg.draw.rect(screen,(15,15,15),
                                (base_left_pos+screen_size[0]/div/2-40+2,
                                block_height+text_delta*len(block_set)+2,78,28))
                pg.draw.rect(screen,(50,50,50),
                                (base_left_pos+screen_size[0]/div/2-40+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,78,28))
                pg.draw.rect(screen,(100,100,100),
                                (base_left_pos+screen_size[0]/div/2-40+2+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,74,24))
                text = font.render("Delete",True,text_black)
                screen.blit(text, (base_left_pos+screen_size[0]/div/2-text.get_width()/2+2*is_on_button, block_height+text_delta*len(block_set)+14+2*is_on_button-text.get_height()/2))

                is_on_button = (base_left_pos+screen_size[0]/div/2+120-70 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2+120) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0] and sdk_params["element_pointer"] != -1

                pg.draw.rect(screen,(15,15,15),
                                (base_left_pos+screen_size[0]/div/2+120-70+2,
                                block_height+text_delta*len(block_set)+2,68,28))
                pg.draw.rect(screen,(50,50,50),
                                (base_left_pos+screen_size[0]/div/2+120-70+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,68,28))
                pg.draw.rect(screen,(100,100,100),
                                (base_left_pos+screen_size[0]/div/2+120-70+2+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,64,24))
                text = font.render("Edit",True,text_black)
                screen.blit(text, (base_left_pos+screen_size[0]/div/2+120-68/2-text.get_width()/2+2*is_on_button, block_height+text_delta*len(block_set)+14+2*is_on_button-text.get_height()/2))
            
            is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (block_height+(text_height+2)*len(block_set) <= m_pos[1] <= block_height+text_delta*len(block_set)+30) and m_btn[0]
            pg.draw.rect(screen,(15,15,15),
                            (base_left_pos+screen_size[0]/div-30-10+2,
                            block_height+text_delta*len(block_set)+2,28,28))
            pg.draw.rect(screen,(50,50,50),
                            (base_left_pos+screen_size[0]/div-30-10+2*is_on_button,
                            block_height+text_delta*len(block_set)+2*is_on_button,28,28))
            pg.draw.rect(screen,(100,100,100),
                            (base_left_pos+screen_size[0]/div-30-10+2+2*is_on_button,
                            block_height+text_delta*len(block_set)+2+2*is_on_button,24,24))
            pg.draw.polygon(screen,text_black,
                            (
                                (base_left_pos+screen_size[0]/div-30-10+22+2*is_on_button,
                                block_height+text_delta*len(block_set)+14+2*is_on_button),
                                (base_left_pos+screen_size[0]/div-30-10+6+2*is_on_button,
                                block_height+text_delta*len(block_set)+6+2*is_on_button),
                                (base_left_pos+screen_size[0]/div-30-10+6+2*is_on_button,
                                block_height+text_delta*len(block_set)+22+2*is_on_button),
                            ))
        
        if pg.K_EQUALS in keydowns: sdk_params["scale"]+=1
        elif pg.K_MINUS in keydowns: sdk_params["scale"]-=(1 if sdk_params["scale"] > 1 else 0)
        if pressed[pg.K_ESCAPE]:
            sdk_params = {
                "folder_list":[],
                "folder_pointer":-1,
                "consist_pointer":-1,
                "scale":4,
                "editing":False
            }
            sdk_loaded_pack = {"graphics":{},"info":{}}
            screen_state = "title"

        if m_pos[0] >= base_left_pos:
            is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (folder_height+text_delta*len(sdk_menu_blocks[0][2]) <= m_pos[1] <= folder_height+text_delta*len(sdk_menu_blocks[0][2])+30) and m_btn[0]
            if is_on_button and mouse_clicked:
                sdk_params["folder_pointer"]=(sdk_params["folder_pointer"]-1)%len(sdk_params["folder_list"])
                sdk_params["consist_pointer"] = -1
                sdk_params["editing"] = False
                sdk_loaded_pack = {"graphics":{},"info":{},"pos":[0,0],"selection":(-1,-1,0,0)}


            is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (folder_height+text_delta*len(sdk_menu_blocks[0][2]) <= m_pos[1] <= folder_height+text_delta*len(sdk_menu_blocks[0][2])+30) and m_btn[0]
            if is_on_button and mouse_clicked:
                sdk_params["folder_pointer"]=(sdk_params["folder_pointer"]-1)%len(sdk_params["folder_list"])
                sdk_params["consist_pointer"] = -1
                sdk_params["editing"] = False
                sdk_loaded_pack = {"graphics":{},"info":{},"pos":[0,0],"selection":(-1,-1,0,0)}

            is_on_button = (base_left_pos+screen_size[0]/div/2-120 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2-10) and (folder_height+text_delta*len(sdk_menu_blocks[0][2]) <= m_pos[1] <= folder_height+(text_height+2)*len(sdk_menu_blocks[0][2])+30) and m_btn[0] and sdk_params["folder_pointer"] != -1
            if is_on_button and mouse_clicked:
                with open(os.path.join(CURRENT_DIRECTORY,"paks",sdk_params["folder_list"][sdk_params["folder_pointer"]],"pack.json"),encoding="utf-8") as file:
                    pack_parameters = json.loads(file.read())
                    if "consists" in pack_parameters:
                        sdk_params["consist_pointer"] = -1
                        sdk_loaded_pack["info"] = pack_parameters["consists"]
                        sdk_loaded_pack["pos"]=[0,0]
                        sdk_loaded_pack["selection"]=(-1,-1,0,0)
                    else:
                        sdk_params["consist_pointer"] = -1
                        sdk_loaded_pack = {"graphics":{},"info":{},"pos":[0,0],"selection":(-1,-1,0,0)}
            
            is_on_button = (base_left_pos+screen_size[0]/div/2+10 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2+120) and (folder_height+text_delta*len(sdk_menu_blocks[0][2]) <= m_pos[1] <= folder_height+(text_height+2)*len(sdk_menu_blocks[0][2])+30) and m_btn[0] and sdk_params["folder_pointer"] != -1 and sdk_loaded_pack["info"] != {}
            if is_on_button and mouse_clicked:
                pack_parameters = ""
                with open(os.path.join(CURRENT_DIRECTORY,"paks",sdk_params["folder_list"][sdk_params["folder_pointer"]],"pack.json"),encoding="utf-8") as file:
                    pack_parameters = json.loads(file.read())
                
                pack_parameters["consists"] = sdk_loaded_pack["info"]

                with open(os.path.join(CURRENT_DIRECTORY,"paks",sdk_params["folder_list"][sdk_params["folder_pointer"]],"pack.json"),"w",encoding="utf-8") as file:
                    json.dump(pack_parameters, file, ensure_ascii=False, sort_keys=True,indent=4)

            if len(sdk_menu_blocks) == 3:
                is_on_button = (base_left_pos+screen_size[0]/div/2-120 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2-120+70) and (element_height+text_delta*len(sdk_menu_blocks[2][2]) <= m_pos[1] <= element_height+(text_height+2)*len(sdk_menu_blocks[2][2])+30) and m_btn[0]

                if is_on_button and mouse_clicked:
                    sprite_id = 0
                    while f"sprite_{sprite_id}" in sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"]:
                        sprite_id+=1
                    sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"][f"sprite_{sprite_id}"] = {
                        "x":0,
                        "y":0,
                        "w":1,
                        "h":1,
                        "scale":1
                    }
                    sdk_params["element_pointer"] = list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys()).index(f"sprite_{sprite_id}")
                    
                
                is_on_button = (base_left_pos+screen_size[0]/div/2-40 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2+40) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0] and sdk_params["element_pointer"] != -1

                if is_on_button and mouse_clicked:
                    key = list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys())[sdk_params["element_pointer"]]
                    sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].pop(key)
                    sdk_params["element_pointer"] = min(sdk_params["element_pointer"],len(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"])-1) 


                is_on_button = (base_left_pos+screen_size[0]/div/2+120-70 <= m_pos[0] <= base_left_pos+screen_size[0]/div/2+120) and (element_height+text_delta*len(sdk_menu_blocks[2][2]) <= m_pos[1] <= element_height+(text_height+2)*len(sdk_menu_blocks[2][2])+30) and m_btn[0] and sdk_params["element_pointer"] != -1

                if is_on_button and mouse_clicked:
                    sdk_params["editing"] = True

            if sdk_loaded_pack["info"] != {}:
                is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (consist_height+text_delta*len(sdk_menu_blocks[1][2]) <= m_pos[1] <= consist_height+text_delta*len(sdk_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    sdk_params["consist_pointer"]=(sdk_params["consist_pointer"]-1)%len(sdk_loaded_pack["info"])
                    sdk_params["element_pointer"] = -1
                    sdk_loaded_pack["graphics"]["panel"] = pg.image.load(
                        os.path.join(*([CURRENT_DIRECTORY,"paks",sdk_params["folder_list"][sdk_params["folder_pointer"]],sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_sprite"]]))).convert_alpha()

                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (consist_height+text_delta*len(sdk_menu_blocks[1][2]) <= m_pos[1] <= consist_height+text_delta*len(sdk_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    sdk_params["consist_pointer"]=(sdk_params["consist_pointer"]+1)%len(sdk_loaded_pack["info"])
                    sdk_params["element_pointer"] = -1
                    sdk_loaded_pack["graphics"]["panel"] = pg.image.load(
                        os.path.join(*([CURRENT_DIRECTORY,"paks",sdk_params["folder_list"][sdk_params["folder_pointer"]],sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_sprite"]]))).convert_alpha()
                    
            if sdk_params["consist_pointer"] != -1:
                is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (element_height+text_delta*len(sdk_menu_blocks[1][2]) <= m_pos[1] <= element_height+text_delta*len(sdk_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    sdk_params["element_pointer"]=(sdk_params["element_pointer"]-1)%len(list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys()))
                    sdk_params["editing"] = False

                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (element_height+text_delta*len(sdk_menu_blocks[1][2]) <= m_pos[1] <= element_height+text_delta*len(sdk_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    sdk_params["element_pointer"]=(sdk_params["element_pointer"]+1)%len(list(sdk_loaded_pack["info"][sdk_params["consist_pointer"]]["control_panel_info"].keys()))
                    sdk_params["editing"] = False



    elif screen_state == "editor":
        editor_block_size = (128,512)
        iconbar_height = 140
        iconbar_size = (64,128)
        textbox_length = 280

        screen.fill(tunnel_nothingness)
        block_pos = [int((player_pos[0]-(editor_block_size[0] if player_pos[0] < 0 else 0))/editor_block_size[0]),
                     int((player_pos[1]-(editor_block_size[1] if player_pos[1] < 0 else 0))/editor_block_size[1])]
        
        for block_x in range(-1-int(screen_size[0]/editor_block_size[0]),int(screen_size[0]/editor_block_size[0])+2):
            for block_y in range(-1-int(screen_size[1]/editor_block_size[1]),int(screen_size[1]/editor_block_size[1])+2):
                tile_world_position = (block_pos[0]+block_x,block_pos[1]+block_y)
                pg.draw.rect(screen,(30,30,30),(screen_size[0]/2+block_x*editor_block_size[0]-player_pos[0]%editor_block_size[0],
                                                    screen_size[1]/2+block_y*editor_block_size[1]-player_pos[1]%editor_block_size[1],
                                                    editor_block_size[0],
                                                    editor_block_size[1]
                            ),4
                            
                )
                if tile_world_position in world:
                    if world[tile_world_position][0] in icons:
                        screen.blit(pg.transform.scale(icons[world[tile_world_position][0]],editor_block_size
                                ),(
                                screen_size[0]/2+block_x*editor_block_size[0]-player_pos[0]%editor_block_size[0],
                                screen_size[1]/2+block_y*editor_block_size[1]-player_pos[1]%editor_block_size[1])
                            )
                    else:
                        icon = None
                        text = None
                        if world[tile_world_position][0][-8:] == "platform": 
                            icon = "generic_st_platform"
                            text = world[tile_world_position][0][:-8]
                        elif world[tile_world_position][0][-10:] == "platform_f": 
                            icon = "generic_st_platform_f"
                            text = world[tile_world_position][0][:-10]
                        elif world[tile_world_position][0][-10:] == "track_tstr": 
                            icon = "generic_st_track"
                            text = world[tile_world_position][0][:-10]
                        elif world[tile_world_position][0][-12:] == "track_f_tstr": 
                            icon = "generic_st_track_f"
                            text = world[tile_world_position][0][:-12]
                        elif world[tile_world_position][0][-4:] == "tstr": icon = "default_tstr"
                        elif world[tile_world_position][0][-4:] == "tca1": icon = "default_tca1"
                        elif world[tile_world_position][0][-4:] == "tca2": icon = "default_tca2"
                        elif world[tile_world_position][0][-4:] == "tcb1": icon = "default_tcb1"
                        elif world[tile_world_position][0][-4:] == "tcb2": icon = "default_tcb2"
                        elif world[tile_world_position][0][-4:] == "tsa1": icon = "default_tsa1"
                        elif world[tile_world_position][0][-4:] == "tsa2": icon = "default_tsa2"
                        elif world[tile_world_position][0][-4:] == "tsb1": icon = "default_tsb1"
                        elif world[tile_world_position][0][-4:] == "tsb2": icon = "default_tsb2"
                        if icon:
                            screen.blit(pg.transform.scale(icons[icon],editor_block_size
                                ),(
                                screen_size[0]/2+block_x*editor_block_size[0]-player_pos[0]%editor_block_size[0],
                                screen_size[1]/2+block_y*editor_block_size[1]-player_pos[1]%editor_block_size[1])
                            )
                        if text:
                            if text[-1] == "_": text = text[:-1]
                            text = font.render(text, True,(60,60,60))
                            text = pg.transform.rotate(text,-90)
                            screen.blit(text,(
                                screen_size[0]/2+(block_x+0.5)*editor_block_size[0]-player_pos[0]%editor_block_size[0]-text.get_width()/2,
                                screen_size[1]/2+(block_y+0.5)*editor_block_size[1]-player_pos[1]%editor_block_size[1]-text.get_height()/2)
                            )
        
        pg.draw.rect(screen,(75,75,75),(0,screen_size[1]-iconbar_height,screen_size[0],iconbar_height))
        for item_pos, item in enumerate(toolbar[current_toolbar]):
            w,h = icons[item].get_size()
            surf = icons[item].subsurface((
                (w-min(w,h))/2,
                (h-min(w,h)*(iconbar_size[1]/iconbar_size[0]))/2,
                min(w,h),
                min(w,h)*(iconbar_size[1]/iconbar_size[0])
            ))

            pg.draw.rect(screen,(125,125,125) if current_tool != item_pos else (175,175,175),(
                screen_size[0]/2+(iconbar_size[0]+16)*(item_pos-len(toolbar[current_toolbar])/2),
                screen_size[1]-iconbar_height/2-iconbar_size[1]/2,
                iconbar_size[0],
                iconbar_size[1]
                ))
            screen.blit(pg.transform.scale(surf,iconbar_size),(
                screen_size[0]/2+(iconbar_size[0]+16)*(item_pos-len(toolbar[current_toolbar])/2),
                screen_size[1]-iconbar_height/2-iconbar_size[1]/2
                )
            )
        
        text = font.render(custom_tool_parameters[0]+" ",True,(10,10,10))
        textbox_height = text.get_height()+4
        pg.draw.rect(screen,(200,200,200) if custom_tool_parameters[2] != 1 else (220,220,220),(screen_size[0]-textbox_length-20,screen_size[1]-iconbar_height/2-textbox_height*1.5,textbox_length,textbox_height))
        screen.blit(text,(screen_size[0]-textbox_length-18,screen_size[1]-iconbar_height/2-textbox_height*1.5+2))
        text = font.render(custom_tool_parameters[1]+" ",True,(10,10,10))
        pg.draw.rect(screen,(200,200,200) if custom_tool_parameters[2] != 2 else (220,220,220),(screen_size[0]-textbox_length-20,screen_size[1]-iconbar_height/2+textbox_height*0.5,textbox_length,textbox_height))
        screen.blit(text,(screen_size[0]-textbox_length-18,screen_size[1]-iconbar_height/2+textbox_height*0.5+2))

        
        pressed = pg.key.get_pressed()
        m_pos = pg.mouse.get_pos()
        m_btn = pg.mouse.get_pressed()

        if m_btn[0] or m_btn[1] or m_btn[2]:
            if m_pos[1] < screen_size[1]-iconbar_height:
                m_world_pos = (player_pos[0]+m_pos[0]-screen_size[0]/2,
                               player_pos[1]+m_pos[1]-screen_size[1]/2)
                m_block_pos = (int((m_world_pos[0]-(editor_block_size[0] if m_world_pos[0] < 0 else 0))/editor_block_size[0]),
                            int((m_world_pos[1]-(editor_block_size[1] if m_world_pos[1] < 0 else 0))/editor_block_size[1]))
                if m_btn[0] and current_tool != -1 and m_block_pos not in world:
                    if toolbar[current_toolbar][current_tool] != "custom_tile":
                        world[m_block_pos] = [toolbar[current_toolbar][current_tool]]
                        if toolbar[current_toolbar][current_tool][-4:-1] in ["tsa","tsb"]:
                            switches[m_block_pos] = False
                    else:
                        world[m_block_pos] = [custom_tool_parameters[0],custom_tool_parameters[1]]
                        if custom_tool_parameters[0][-4:-1] in ["tsa","tsb"]:
                            switches[m_block_pos] = False
                elif m_btn[2] and m_block_pos in world:
                    world.pop(m_block_pos)
                    if m_block_pos in switches:
                        switches.pop(m_block_pos)
            elif mouse_clicked:
                for item_pos, item in enumerate(toolbar[current_toolbar]):
                    if (screen_size[0]/2+(iconbar_size[0]+16)*(item_pos-len(toolbar[current_toolbar])/2) <= m_pos[0] and
                        screen_size[0]/2+(iconbar_size[0]+16)*(item_pos-len(toolbar[current_toolbar])/2)+iconbar_size[0] >= m_pos[0] and
                        screen_size[1]-iconbar_height <= m_pos[1] and
                        screen_size[1] >= m_pos[1]):
                        if item_pos == current_tool: current_tool = -1
                        else: current_tool = item_pos
                
                if current_tool != -1 and toolbar[current_toolbar][current_tool] == "custom_tile":
                    text = font.render(custom_tool_parameters[0]+" ",True,(10,10,10))
                    if (screen_size[0]-textbox_length-20 <= m_pos[0] and
                        screen_size[0]-20 >= m_pos[0] and
                        screen_size[1]-iconbar_height/2-textbox_height*1.5 <= m_pos[1] and
                        screen_size[1]-iconbar_height/2-textbox_height*0.5 >= m_pos[1]):
                        custom_tool_parameters[2] = 1 if custom_tool_parameters[2] != 1 else 0
                    elif (screen_size[0]-textbox_length-20 <= m_pos[0] and
                        screen_size[0]-20 >= m_pos[0] and
                        screen_size[1]-iconbar_height/2+textbox_height*0.5 <= m_pos[1] and
                        screen_size[1]-iconbar_height/2+textbox_height*1.5 >= m_pos[1]):
                        custom_tool_parameters[2] = 2 if custom_tool_parameters[2] != 2 else 0
 
        speed = 16 if pressed[pg.K_RSHIFT] or pressed[pg.K_LSHIFT] else 4
        if pressed[pg.K_DOWN]: 
            player_pos[1]+=speed*clock.get_fps()/60
        if pressed[pg.K_UP]: 
            player_pos[1]-=speed*clock.get_fps()/60
        if pressed[pg.K_LEFT]: 
            player_pos[0]-=speed*clock.get_fps()/60
        if pressed[pg.K_RIGHT]: 
            player_pos[0]+=speed*clock.get_fps()/60
        if pg.K_ESCAPE in keydowns:
            screen_state = "title"
        if pg.K_d in keydowns:
            pprint.pprint(world)
            pprint.pprint(switches)
                
    
    elif screen_state == "playing":
        valid = []
        valid_draw = {}
        for train_id in trains:
            trains[train_id].switches = switches
            train = trains[train_id]
            if (player_pos[0]-screen_size[0]*2 <= train.pos[0] <= player_pos[0]+screen_size[0]*2) and (player_pos[1]-screen_size[1]*2 <= train.pos[1] <= player_pos[1]+screen_size[1]*2):
                valid.append([train_id,train.pos[1]])
                if not int(((train.pos[0]-train.size[0]/2)//block_size[0])-(1 if (train.pos[0]-train.size[0]/2)<0 else 0)) in valid_draw:
                    valid_draw[int(((train.pos[0]-train.size[0]/2)//block_size[0])-(1 if (train.pos[0]-train.size[0]/2)<0 else 0))] = []
                valid_draw[int(((train.pos[0]-train.size[0]/2)//block_size[0])-(1 if (train.pos[0]-train.size[0]/2)<0 else 0))].append(
                    [
                        (train.pos[0],train.pos[1]),
                        train.type,
                        train.angle,
                        train.reversed,
                        train.size,
                        consists[train.consist].doors
                ])
        if controlling != -1: player_pos = [trains[controlling].pos[0],trains[controlling].pos[1]-screen_size[1]/8*2*(1 if 90 <= (trains[controlling].angle+trains[controlling].reversed*180)%360 <= 270 else -1)]
        block_pos = [int((player_pos[0]-(block_size[0] if player_pos[0] < 0 else 0))/block_size[0]),int((player_pos[1]-(block_size[1] if player_pos[1] < 0 else 0))/block_size[1])]
    
        screen.fill(tunnel_nothingness)
        prima_object_draw_queue = []
        object_draw_queue = []
        for tile_x in reversed(range(-int(screen_size[0]/block_size[0])-2,int(screen_size[0]/block_size[0])+3)):
            for tile_y in range(-int(screen_size[1]/block_size[1])-2,int(screen_size[1]/block_size[1])+3):
                #pg.draw.rect(screen,(255,0,0),)
                x_offset = (block_pos[0]+tile_x)*block_size[0]
                y_offset = (block_pos[1]+tile_y)*block_size[1]

                if (block_pos[0]+tile_x,block_pos[1]+tile_y) in world:
                    tile_world_position = (block_pos[0]+tile_x,block_pos[1]+tile_y)

                    if world[tile_world_position][0] in ground_sprites:
                        prima_object_draw_queue.append([
                            "world",
                            (x_offset,y_offset),
                            world[tile_world_position][0],
                            (
                                tile_x*block_size[0],
                                tile_y*block_size[1]
                            ),
                            tile_world_position

                        ])
                    if len(world[tile_world_position]) > 1 and world[tile_world_position][1] in ground_sprites:
                        for z in range(4):
                            object_draw_queue.append([
                                "world",
                                (x_offset,y_offset+block_size[1]/4*z),
                                world[tile_world_position][1],z,
                                (
                                    tile_x*block_size[0],
                                    tile_y*block_size[1]+block_size[1]/4*z
                                )

                            ])
        for object in sorted(prima_object_draw_queue,key= lambda z:(z[1][1],-z[1][0])):
            if object[0] == "world":
                w, h = ground_sprites[object[2]][world_angle].get_size()
                x_offset = object[3][0]+block_size[0]/2-player_pos[0]%(block_size[0])
                y_offset = object[3][1]+block_size[1]/2-player_pos[1]%(block_size[1])
                screen.blit(
                    ground_sprites[object[2]][world_angle]
                    ,(round(screen_size[0]/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle))-w/2,0),
                    round(screen_size[1]/2+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-ground_sprites[object[2]]["height"]/compression-h/2,0)
                    )
                )
                if mouse_block_pos[0] == object[4][0] and mouse_block_pos[1] == object[4][1] and object[2][-4:-1] in ["tsa","tsb"]:
                    x_offset = object[3][0]-player_pos[0]%(block_size[0])+block_size[0]/2
                    x_offset1 = object[3][0]-player_pos[0]%(block_size[0])
                    x_offset2 = object[3][0]-player_pos[0]%(block_size[0])
                    x_offset3 = object[3][0]-player_pos[0]%(block_size[0])+block_size[0]
                    x_offset4 = object[3][0]-player_pos[0]%(block_size[0])+block_size[0]
                    y_offset = object[3][1]-player_pos[1]%(block_size[1])+block_size[1]/2
                    y_offset1 = object[3][1]-player_pos[1]%(block_size[1])
                    y_offset2 = object[3][1]-player_pos[1]%(block_size[1])+block_size[1]
                    y_offset3 = object[3][1]-player_pos[1]%(block_size[1])+block_size[1]
                    y_offset4 = object[3][1]-player_pos[1]%(block_size[1])
                    pg.draw.polygon(screen,((0,0,255) if switches[mouse_block_pos] else (0,255,0)),(
                            (
                                screen_size[0]/2+x_offset1*math.cos(math.radians(360-world_angle))-y_offset1*math.sin(math.radians(360-world_angle)),
                                screen_size[1]/2+(x_offset1*math.sin(math.radians(360-world_angle))+y_offset1*math.cos(math.radians(360-world_angle)))/compression 
                            ),(
                                screen_size[0]/2+x_offset2*math.cos(math.radians(360-world_angle))-y_offset2*math.sin(math.radians(360-world_angle)),
                                screen_size[1]/2+(x_offset2*math.sin(math.radians(360-world_angle))+y_offset2*math.cos(math.radians(360-world_angle)))/compression 
                            ),(
                                screen_size[0]/2+x_offset3*math.cos(math.radians(360-world_angle))-y_offset3*math.sin(math.radians(360-world_angle)),
                                screen_size[1]/2+(x_offset3*math.sin(math.radians(360-world_angle))+y_offset3*math.cos(math.radians(360-world_angle)))/compression 
                            ),(
                                screen_size[0]/2+x_offset4*math.cos(math.radians(360-world_angle))-y_offset4*math.sin(math.radians(360-world_angle)),
                                screen_size[1]/2+(x_offset4*math.sin(math.radians(360-world_angle))+y_offset4*math.cos(math.radians(360-world_angle)))/compression 
                            )
                        ),10)
            

        for z in valid_draw:
            for i, train_params in enumerate(sorted(valid_draw[z],key=lambda x:x[1])):
                angle = (train_params[2]+world_angle)%360
                w, h = train_params[4][0]*0,train_params[4][1]*0
                x_offset = train_params[0][0]+(w*math.cos(math.radians(180-train_params[2]))-h*math.sin(math.radians(180-train_params[2])))
                y_offset = train_params[0][1]+(w*math.sin(math.radians(180-train_params[2]))+h*math.cos(math.radians(180-train_params[2])))
                
                object_draw_queue.append([
                        "train",
                        (x_offset,y_offset),
                        train_params[1],
                        (angle+train_params[3]*180)%360,
                        (x_offset -train_params[0][0],
                        y_offset -train_params[0][1]),
                        train_params[5], train_params[3]
                    ])
                    
        for object in sorted(object_draw_queue,key= lambda z:(z[1][1]-z[1][0])):
            if object[0] == "world":
                w, h = ground_sprites[object[2]][object[3]].get_size()
                x_offset = object[4][0]+block_size[0]/2-player_pos[0]%(block_size[0])
                y_offset = object[4][1]+block_size[1]/8-player_pos[1]%(block_size[1])
                screen.blit(
                    #pg.transform.scale(
                    ground_sprites[object[2]][object[3]]#,block_size)
                    ,(round(screen_size[0]/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle))-w/2,0),
                    round(screen_size[1]/2+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-ground_sprites[object[2]]["height"]/compression-h/2,0)
                    )
                )
            elif object[0] == "train":
                r_train_sprite = train_sprites["sprites"][object[2]][object[5]["r" if object[6] else "l"]][object[3]]["r"]
                r_height = train_sprites["sprites"][object[2]][object[5]["r" if object[6] else "l"]]["height"]
                l_train_sprite = train_sprites["sprites"][object[2]][object[5]["l" if object[6] else "r"]][object[3]]["l"]
                l_height = train_sprites["sprites"][object[2]][object[5]["l" if object[6] else "r"]]["height"]
                if 0 <= object[3] < 90 or 270 <= object[3] < 360:
                    x_offset = -player_pos[0]+object[1][0]-object[4][0]
                    y_offset = -player_pos[1]+object[1][1]-object[4][1]
                    screen.blit(
                        r_train_sprite,
                        (
                            round(screen_size[0]/2-r_train_sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),0),
                            round(screen_size[1]/2-r_train_sprite.get_height()/2-r_height/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6,0)
                        )
                    )
                    x_offset = -player_pos[0]+object[1][0]-object[4][0]
                    y_offset = -player_pos[1]+object[1][1]-object[4][1]
                    screen.blit(
                        l_train_sprite,
                        (
                            round(screen_size[0]/2-l_train_sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),0),
                            round(screen_size[1]/2-l_train_sprite.get_height()/2-l_height/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6,0)
                        )
                    )
                else:
                    x_offset = -player_pos[0]+object[1][0]-object[4][0]
                    y_offset = -player_pos[1]+object[1][1]-object[4][1]
                    screen.blit(
                        l_train_sprite,
                        (
                            round(screen_size[0]/2-l_train_sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),0),
                            round(screen_size[1]/2-l_train_sprite.get_height()/2-l_height/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6,0)
                        )
                    )
                    x_offset = -player_pos[0]+object[1][0]-object[4][0]
                    y_offset = -player_pos[1]+object[1][1]-object[4][1]
                    screen.blit(
                        r_train_sprite,
                        (
                            round(screen_size[0]/2-r_train_sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),0),
                            round(screen_size[1]/2-r_train_sprite.get_height()/2-r_height/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6,0)
                        )
                    )
        
        if debug > 1:
            for tile_y in range(-int(screen_size[1]/block_size[1]/2)-1,int(screen_size[1]/block_size[1]/2)+2):
                for tile_x in reversed(range(-int(screen_size[0]/block_size[0]/2)-1,int(screen_size[0]/block_size[0]/2)+2)):
                    x_offset = tile_x*block_size[0]-player_pos[0]%(block_size[0])+block_size[0]/2
                    y_offset = tile_y*block_size[1]-player_pos[1]%(block_size[1])+block_size[1]/2
                    x_offset1 = tile_x*block_size[0]-player_pos[0]%(block_size[0])
                    y_offset1 = tile_y*block_size[1]-player_pos[1]%(block_size[1])
                    x_offset2 = tile_x*block_size[0]-player_pos[0]%(block_size[0])
                    y_offset2 = tile_y*block_size[1]-player_pos[1]%(block_size[1])+block_size[1]
                    x_offset3 = tile_x*block_size[0]-player_pos[0]%(block_size[0])+block_size[0]
                    y_offset3 = tile_y*block_size[1]-player_pos[1]%(block_size[1])+block_size[1]
                    x_offset4 = tile_x*block_size[0]-player_pos[0]%(block_size[0])+block_size[0]
                    y_offset4 = tile_y*block_size[1]-player_pos[1]%(block_size[1])
                    pg.draw.polygon(screen,(255,0,0,),(
                        (
                            screen_size[0]/2+x_offset1*math.cos(math.radians(360-world_angle))-y_offset1*math.sin(math.radians(360-world_angle)),
                            screen_size[1]/2+(x_offset1*math.sin(math.radians(360-world_angle))+y_offset1*math.cos(math.radians(360-world_angle)))/compression 
                        ),(
                            screen_size[0]/2+x_offset2*math.cos(math.radians(360-world_angle))-y_offset2*math.sin(math.radians(360-world_angle)),
                            screen_size[1]/2+(x_offset2*math.sin(math.radians(360-world_angle))+y_offset2*math.cos(math.radians(360-world_angle)))/compression 
                        ),(
                            screen_size[0]/2+x_offset3*math.cos(math.radians(360-world_angle))-y_offset3*math.sin(math.radians(360-world_angle)),
                            screen_size[1]/2+(x_offset3*math.sin(math.radians(360-world_angle))+y_offset3*math.cos(math.radians(360-world_angle)))/compression 
                        ),(
                            screen_size[0]/2+x_offset4*math.cos(math.radians(360-world_angle))-y_offset4*math.sin(math.radians(360-world_angle)),
                            screen_size[1]/2+(x_offset4*math.sin(math.radians(360-world_angle))+y_offset4*math.cos(math.radians(360-world_angle)))/compression 
                        )
                    ),4)
                    text =annotation_font.render(f"{block_pos[0]+tile_x},{block_pos[1]+tile_y}",True,(255,255,255))
                    screen.blit(text,(
                        screen_size[0]/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle))+text.get_width()/2,
                        screen_size[1]/2+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression+text.get_height()/2
                    ))
            
        
            #pg.draw.circle(screen,(255,0,0),(-player_pos[0]+train.pos[0]+screen_size[0]/2,-player_pos[1]+train.pos[1]+screen_size[1]/2),4)
        
        
        pressed = pg.key.get_pressed()
        m_btn = pg.mouse.get_pressed()
        m_pos = pg.mouse.get_pos()
        dx, dy = m_pos[0]-screen_size[0]/2, m_pos[1]-screen_size[1]/2
        a, b, c, d =math.cos(math.radians(360-world_angle)),math.sin(math.radians(360-world_angle)),math.sin(math.radians(360-world_angle))/compression,math.cos(math.radians(360-world_angle))/compression
        ty = (dy*a-dx*c)/(a*d+b*c)
        tx = (dx+ty*b)/a
        world_mouse_coord = [tx,ty]
        mouse_block_pos = (
            int((player_pos[0]+world_mouse_coord[0])/block_size[0]-(1 if player_pos[0]+world_mouse_coord[0] < 0 else 0)),
            int((player_pos[1]+world_mouse_coord[1])/block_size[1]-(1 if player_pos[1]+world_mouse_coord[1] < 0 else 0)))
        if m_btn[0] and mouse_clicked and not spawn_menu[0]:
            if mouse_block_pos in world and mouse_block_pos in switches:
                switches[mouse_block_pos] = not(switches[mouse_block_pos])

        if mouse_clicked and m_btn[0] and controlling == -1 and not spawn_menu[0]:
            for temp1 in valid:
                train_id = temp1[0]
                if (trains[train_id].pos[0]-trains[train_id].size[0]/2<=player_pos[0]+world_mouse_coord[0] and
                    player_pos[0]+world_mouse_coord[0]<=trains[train_id].pos[0]+trains[train_id].size[0]/2 and
                    trains[train_id].pos[1]-trains[train_id].size[1]/2<=player_pos[1]+world_mouse_coord[1] and
                    player_pos[1]+world_mouse_coord[1]<=trains[train_id].pos[1]+trains[train_id].size[1]/2):
                    controlling = train_id
                    controlling_consist = trains[train_id].consist

        annotation = None

        if controlling != -1:
            
            found = False
            for map_id, mapping in enumerate(consists[controlling_consist].consist_info["drive_sounds"]):
                if mapping[1] <= consists[controlling_consist].velocity*3.6 and consists[controlling_consist].velocity*3.6 <= mapping[2]:
                    if map_id != consists[controlling_consist].current_roll_sound:
                        consists[controlling_consist].current_roll_sound = map_id
                        channel_rolling.set_volume(0.125)
                        channel_rolling.play(sounds[consists[controlling_consist].train_type][mapping[0]],-1)
                    found = True
            if not found: 
                consists[controlling_consist].current_roll_sound = -1
                channel_rolling.stop()



            panel = train_sprites["controls"][consists[controlling_consist].train_type]["panel"]

            hotkeys_check = [pressed[hotkeys[key]] or hotkeys[key] in keyups for key in hotkeys]

            if (screen_size[0]/2+panel.get_width()/2 >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2 and 
                screen_size[1] >= m_pos[1] >= screen_size[1]-panel.get_height() or True) or True in hotkeys_check:
                for elem_id, element in enumerate(consists[controlling_consist].consist_info["element_mapouts"]):
                    #if element["type"] != "analog_scale":
                    info = element["draw_mappings"][element["state"] if "state" in element else 0]
                    x,y,w,h = info[0], info[1],info[4], info[5]
                    scale = info[2]
                    if (screen_size[0]/2-panel.get_width()/2+x*scale+w*scale >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2+x*scale and 
                        screen_size[1]-panel.get_height()+y*scale+h*scale >= m_pos[1] >= screen_size[1]-panel.get_height()+y*scale) or hotkeys_check: 
                        if (screen_size[0]/2-panel.get_width()/2+x*scale+w*scale >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2+x*scale and 
                        screen_size[1]-panel.get_height()+y*scale+h*scale >= m_pos[1] >= screen_size[1]-panel.get_height()+y*scale):
                            annotation = element["name"] if element["type"] != "analog_scale" else element["name"].replace("%s",str(element["angle"]))
                        if element["type"] in ["button","switch"]:
                            self_hotkey = hotkeys[element["connection"]] if element["connection"] in hotkeys else None
                            if (screen_size[0]/2-panel.get_width()/2+x*scale+w*scale >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2+x*scale and 
                                screen_size[1]-panel.get_height()+y*scale+h*scale >= m_pos[1] >= screen_size[1]-panel.get_height()+y*scale and (m_btn[0] or mouse_clicked )) or (self_hotkey != None and pressed[self_hotkey]):
                                if element["type"] == "button" and (m_btn[0] and element["state"] != element["default"] or mouse_clicked or self_hotkey != None and pressed[self_hotkey]):
                                    consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] = not(element["default"])
                                    #print(element["connection"],"left_doors",element["connection"] == "left_doors",trains[controlling].reversed,element["connection"] == "left_doors" and trains[controlling].reversed)
                                    if element["connection"] == "left_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["right_doors"] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    elif element["connection"] == "right_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["left_doors"] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    elif element["connection"] not in ["left_doors","right_doors"] or not trains[controlling].reversed:
                                        consists[controlling_consist].control_wires[element["connection"]] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    if (mouse_clicked or self_hotkey in keydowns) and len(element["draw_mappings"][element["state"]]) == 7:
                                        sounds[consists[controlling_consist].train_type][element["draw_mappings"][element["state"]][6]].play()

                                elif element["type"] == "switch" and (mouse_clicked and not mouse_clicked_prev or self_hotkey in keydowns):
                                    consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] = not(consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"])
                                    if element["connection"] == "left_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["right_doors"] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                        a_long_variable_so_it_works_absolutely_not_a_kostyla = annotation_font.render("работать",True,text_color)
                                        screen.blit(a_long_variable_so_it_works_absolutely_not_a_kostyla,(0,0))
                                    elif element["connection"] == "right_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["left_doors"] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    elif element["connection"] not in ["left_doors","right_doors"] or not trains[controlling].reversed:
                                        consists[controlling_consist].control_wires[element["connection"]] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    if len(element["draw_mappings"][element["state"]]) == 7:
                                        sounds[consists[controlling_consist].train_type][element["draw_mappings"][consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]][6]].play()
                            else:
                                if element["type"] == "button":
                                    if consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] != element["default"] and len(element["draw_mappings"][element["default"]]) == 7:
                                        sounds[consists[controlling_consist].train_type][element["draw_mappings"][element["default"]][6]].play()
                                    consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] = element["default"]
                                    if element["connection"] == "left_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["right_doors"] = element["default"]
                                    elif element["connection"] == "right_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["left_doors"] = element["default"]
                                    else:
                                        consists[controlling_consist].control_wires[element["connection"]] = element["default"]
        else:
            pass
                        

                        

        if controlling != -1:
            panel = train_sprites["controls"][consists[controlling_consist].train_type]["panel"]

            if "underlay_draw_params" in consists[controlling_consist].consist_info:
                underlay = train_sprites["controls"][consists[controlling_consist].train_type]["underlay"]
                x,y,scale = consists[controlling_consist].consist_info["underlay_draw_params"]
                screen.blit(underlay,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))

            
            rr_direction = int(consists[controlling_consist].controlling_direction*(1-2*trains[controlling].reversed))
            rr = train_sprites["controls"][consists[controlling_consist].train_type][f"rr_{rr_direction}"]
            x,y = consists[controlling_consist].consist_info["rr_draw_mapouts"][str(rr_direction)]
            scale = consists[controlling_consist].consist_info["rr_draw_mapouts"]["scale"]
            screen.blit(rr,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))

            screen.blit(panel,(screen_size[0]/2-panel.get_width()/2,screen_size[1]-panel.get_height()))

            for element in consists[controlling_consist].consist_info["element_mapouts"]:
                if element["type"] != "analog_scale":
                    info = element["draw_mappings"][element["state"]]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = train_sprites["controls"][consists[controlling_consist].train_type][info[3]] 
                        x,y = info[0], info[1]
                        scale = info[2]
                        screen.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
                else:
                    info = element["draw_mappings"][0]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = train_sprites["controls"][consists[controlling_consist].train_type][info[3]] 
                        x,y = info[0], info[1]
                        scale = info[2]
                        screen.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
                    
                    info = element["draw_mappings"][1]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = pg.transform.rotate(train_sprites["controls"][consists[controlling_consist].train_type][info[3]],round(element["base_angle"]-element["multiplier"]*element["angle"],5))
                        local_x,local_y = info[0], info[1]
                        local_scale = info[2]
                        screen.blit(sprite,(round(screen_size[0]/2-panel.get_width()/2+(x*scale+local_x*local_scale)-sprite.get_width()/2,2),float(screen_size[1]-panel.get_height()+(int(y*scale+local_y*local_scale)+0.5)-sprite.get_height()/2)))

                    info = element["draw_mappings"][2]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = train_sprites["controls"][consists[controlling_consist].train_type][info[3]] 
                        x,y = info[0], info[1]
                        scale = info[2]
                        screen.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))


            km = train_sprites["controls"][consists[controlling_consist].train_type]["km"]
            x,y = consists[controlling_consist].consist_info["km_draw_mapouts"][str(consists[controlling_consist].km)]
            scale = consists[controlling_consist].consist_info["km_draw_mapouts"]["scale"]
            screen.blit(km,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
            
            tk = train_sprites["controls"][consists[controlling_consist].train_type]["tk"]
            x,y = consists[controlling_consist].consist_info["tk_draw_mapouts"][str(consists[controlling_consist].tk)]
            scale = consists[controlling_consist].consist_info["tk_draw_mapouts"]["scale"]
            screen.blit(tk,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
            
            overlay = train_sprites["controls"][consists[controlling_consist].train_type]["overlay"]
            screen.blit(overlay,(screen_size[0]/2-overlay.get_width()/2,screen_size[1]-overlay.get_height()))

            if annotation:
                width_max = 0
                lines = []
                for annotation_line in annotation.split("\n"):
                    lines.append(annotation_font.render(annotation_line, True, (255,255,255)))
                    if lines[-1].get_width() > width_max: width_max = lines[-1].get_width() 
                
                s = pg.Surface((width_max+8,(lines[-1].get_height()+2)*len(lines)+6))
                s.set_alpha(128)
                s.fill((0,0,0))
                screen.blit(s, (m_pos[0]+10,m_pos[1]+20))
                for i,e in enumerate(lines):
                    screen.blit(e, (m_pos[0]+10+(8+width_max)/2-e.get_width()/2,
                                    m_pos[1]+24+(lines[-1].get_height()+2)*i))


        if spawn_menu[1] > 0:
            div = 4 
            base_img_height = 200
            pg.draw.rect(screen,(200,200,200),(screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2),0,screen_size[0]/div+128,screen_size[1]))
            spawn_menu_name = font.render(f"Create a consist",True,text_black)
            screen.blit(spawn_menu_name, (screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)+screen_size[0]/div/2-spawn_menu_name.get_width()/2,100))

            sprite = train_sprites["sprites"][spawn_menu[3]]["closed"][world_angle]["r"]
            screen.blit(sprite,(screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)+screen_size[0]/div/2-sprite.get_width()/2,base_img_height))
            sprite = train_sprites["sprites"][spawn_menu[3]]["closed"][world_angle]["l"]
            screen.blit(sprite,(screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)+screen_size[0]/div/2-sprite.get_width()/2,base_img_height))

            #descriptions_texts = train_types[spawn_menu[2]]["name"].split("\n")
            text_height = 20
            text_delta = text_height + 4
            emu_type_height = base_img_height+20+sprite.get_height()
            repaint_height = emu_type_height+text_delta*len(train_types[spawn_menu[2]]["name"].split("\n"))+30+15
            base_left_pos = screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)
            spawn_menu_blocks = [
                [emu_type_height,"EMU type",train_types[spawn_menu[2]]["name"].split("\n")],
                [repaint_height,"EMU repaint",train_sprites["sprites"][spawn_menu[3]]["name"].split("\n")]
            ]
            for z in spawn_menu_blocks:
                block_height, block_name, block_set = z
                pg.draw.rect(screen,(128,128,128),
                    (base_left_pos+5,
                    block_height-5,
                    screen_size[0]/div-10,
                    text_delta*len(block_set)+40
                ))
                for e, i in enumerate(block_set):
                    spawn_menu_text = font.render(i,True,text_black)
                    screen.blit(spawn_menu_text, 
                        (base_left_pos+screen_size[0]/div/2-spawn_menu_text.get_width()/2,
                        block_height+text_delta*e
                    ))

                is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0]
            
                pg.draw.rect(screen,(15,15,15),
                                (base_left_pos+12,
                                block_height+text_delta*len(block_set)+2,28,28))
                pg.draw.rect(screen,(50,50,50),
                                (base_left_pos+10+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,28,28))
                pg.draw.rect(screen,(100,100,100),
                                (base_left_pos+12+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,24,24))
                pg.draw.polygon(screen,text_black,
                                (
                                    (base_left_pos+16+2*is_on_button,
                                    block_height+text_delta*len(block_set)+14+2*is_on_button),
                                    (base_left_pos+10+22+2*is_on_button,
                                    block_height+text_delta*len(block_set)+6+2*is_on_button),
                                    (base_left_pos+10+22+2*is_on_button,
                                    block_height+text_delta*len(block_set)+22+2*is_on_button),
                                ))
                
                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (block_height+(text_height+2)*len(block_set) <= m_pos[1] <= block_height+text_delta*len(block_set)+30) and m_btn[0]
                pg.draw.rect(screen,(15,15,15),
                                (base_left_pos+screen_size[0]/div-30-10+2,
                                block_height+text_delta*len(block_set)+2,28,28))
                pg.draw.rect(screen,(50,50,50),
                                (base_left_pos+screen_size[0]/div-30-10+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,28,28))
                pg.draw.rect(screen,(100,100,100),
                                (base_left_pos+screen_size[0]/div-30-10+2+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,24,24))
                pg.draw.polygon(screen,text_black,
                                (
                                    (base_left_pos+screen_size[0]/div-30-10+22+2*is_on_button,
                                    block_height+text_delta*len(block_set)+14+2*is_on_button),
                                    (base_left_pos+screen_size[0]/div-30-10+6+2*is_on_button,
                                    block_height+text_delta*len(block_set)+6+2*is_on_button),
                                    (base_left_pos+screen_size[0]/div-30-10+6+2*is_on_button,
                                    block_height+text_delta*len(block_set)+22+2*is_on_button),
                                ))
                
            if m_pos[0] >= base_left_pos:
                is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (emu_type_height+text_delta*len(spawn_menu_blocks[0][2]) <= m_pos[1] <= emu_type_height+text_delta*len(spawn_menu_blocks[0][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    spawn_menu[2] = list(consists_info.keys())[list(consists_info.keys()).index(spawn_menu[2])-1]
                    spawn_menu[3] = train_repaint_dictionary[spawn_menu[2]][0]

                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (emu_type_height+text_delta*len(spawn_menu_blocks[0][2]) <= m_pos[1] <= emu_type_height+text_delta*len(spawn_menu_blocks[0][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    spawn_menu[2] = list(consists_info.keys())[(list(consists_info.keys()).index(spawn_menu[2])+1)%len(consists_info.keys())]
                    spawn_menu[3] = train_repaint_dictionary[spawn_menu[2]][0]

                is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (repaint_height+text_delta*len(spawn_menu_blocks[1][2]) <= m_pos[1] <= repaint_height+text_delta*len(spawn_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    spawn_menu[3] = train_repaint_dictionary[spawn_menu[2]][train_repaint_dictionary[spawn_menu[2]].index(spawn_menu[3])-1]

                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (repaint_height+text_delta*len(spawn_menu_blocks[1][2]) <= m_pos[1] <= repaint_height+text_delta*len(spawn_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    spawn_menu[3] = train_repaint_dictionary[spawn_menu[2]][(train_repaint_dictionary[spawn_menu[2]].index(spawn_menu[3])+1)%len(train_repaint_dictionary[spawn_menu[2]])]
                    
            elif controlling == -1:
                if mouse_clicked and m_btn[0]:
                    consist_key = random.randint(0,999)
                    while consist_key in consists: consist_key = random.randint(0,999)
                    consists[consist_key] = Consist(spawn_menu[2],spawn_menu[3],train_types[spawn_menu[2]],consists_info[spawn_menu[2]],consist_key,world,[256*mouse_block_pos[0]+128,player_pos[1]+world_mouse_coord[1]])
                elif mouse_clicked and m_btn[2]:
                    wipe_list = []
                    wipe_list_consists = []
                    for train_id in trains:
                        if mouse_block_pos == (int((trains[train_id].pos[0]-(block_size[0] if trains[train_id].pos[0] < 0 else 0))/block_size[0]),
                                        int((trains[train_id].pos[1]-(block_size[1] if trains[train_id].pos[1] < 0 else 0))/block_size[1])):
                            consist_key = trains[train_id].consist
                            if consist_key not in wipe_list_consists: 
                                wipe_list_consists.append(consist_key)
                                for link in consists[consist_key].linked_to:
                                    wipe_list.append(link)
                    for link in wipe_list_consists:
                        consists[link].exists = False
                        consists.pop(link)
                    for link in wipe_list:
                        trains[link].exists = False
                        trains.pop(link)           

        if controlling == -1:
            speed = 8 if pressed[pg.K_RSHIFT] or pressed[pg.K_LSHIFT] else 2
            if pressed[pg.K_RALT]: speed = 32
            if pressed[pg.K_DOWN]: 
                player_pos[1]+=speed*clock.get_fps()/60
            if pressed[pg.K_UP]: 
                player_pos[1]-=speed*clock.get_fps()/60
            if pressed[pg.K_LEFT]: 
                player_pos[0]-=speed*clock.get_fps()/60
            if pressed[pg.K_RIGHT]: 
                player_pos[0]+=speed*clock.get_fps()/60
            if pg.K_ESCAPE in keydowns:
                screen_state = "title"
                for link in list(consists.keys()):
                    consists[link].exists = False
                    consists.pop(link)
                for link in list(trains.keys()):
                    trains[link].exists = False
                    trains.pop(link)
            if pg.K_s in keydowns:
                spawn_menu[0] = not(spawn_menu[0])
                if spawn_menu[2] == None: 
                    spawn_menu[2] = list(consists_info.keys())[0]
                if spawn_menu[3] == None: 
                    spawn_menu[3] = train_repaint_dictionary[spawn_menu[2]][0]
        else:
            player_pos = [trains[controlling].pos[0],trains[controlling].pos[1]-screen_size[1]/8*2*(1 if 90 <= (trains[controlling].angle+trains[controlling].reversed*180)%360 <= 270 else -1)]

            if pg.K_s in keydowns and spawn_menu[0]:
                spawn_menu[0] = not(spawn_menu[0])

            if pg.K_UP in keydowns and consists[controlling_consist].km < consists[controlling_consist].consist_info["max_km"]:
                consists[controlling_consist].km += 1
                sounds[consists[controlling_consist].train_type]["km_plus"].play()
            elif pg.K_DOWN in keydowns and consists[controlling_consist].km > consists[controlling_consist].consist_info["min_km"]:
                consists[controlling_consist].km -= 1
                sounds[consists[controlling_consist].train_type]["km_minus"].play()

            if pg.K_f in keydowns and consists[controlling_consist].tk < consists[controlling_consist].consist_info["max_tk"]:
                consists[controlling_consist].tk += 1
                sounds[consists[controlling_consist].train_type]["tk_plus"].play()
            elif pg.K_r in keydowns and consists[controlling_consist].tk > consists[controlling_consist].consist_info["min_tk"]:
                consists[controlling_consist].tk -= 1
                sounds[consists[controlling_consist].train_type]["tk_minus"].play()

            if not trains[controlling].reversed:
                if pg.K_0 in keydowns and consists[controlling_consist].km == 0 and consists[controlling_consist].controlling_direction < 1:
                    consists[controlling_consist].controlling_direction += 1
                elif pg.K_9 in keydowns and consists[controlling_consist].km == 0 and consists[controlling_consist].controlling_direction > -1:
                    consists[controlling_consist].controlling_direction -= 1
            else:
                if pg.K_9 in keydowns and consists[controlling_consist].km == 0 and consists[controlling_consist].controlling_direction < 1:
                    consists[controlling_consist].controlling_direction += 1
                elif pg.K_0 in keydowns and consists[controlling_consist].km == 0 and consists[controlling_consist].controlling_direction > -1:
                    consists[controlling_consist].controlling_direction -= 1
            
            
            #print(consists[trains[controlling].consist].velocity)
            
            if pressed[pg.K_ESCAPE]: controlling = -1

        info_blit_list = []
        info_blit_list.append(font.render("alphen's subway simulator "+version,True,text_color))
        info_blit_list.append(font.render("fps: "+str(int(clock.get_fps())), False, ((255 if clock.get_fps() < 45 else 0), (255 if clock.get_fps() > 15 else 0), 0)))
        if debug > 0:
            info_blit_list.append(font.render(f"tramcars: {len(trains)}",True,text_color))
            info_blit_list.append(font.render(f"consists: {len(consists)}",True,text_color))
            info_blit_list.append(font.render(f"pos: {player_pos}",True,text_color))

            if controlling > -1:
                info_blit_list.append(font.render(f"controlling traincar {controlling}",True,text_color))
                info_blit_list.append(font.render(f"controlling traincar {trains[controlling].pos}",True,text_color))
                if debug > 1:
                    info_blit_list.append(font.render(f"velocity {round(consists[controlling_consist].pixel_velocity,5)} px",True,text_color))
                    info_blit_list.append(font.render(f"velocity {round(consists[controlling_consist].velocity,2)} m/s",True,text_color))
                info_blit_list.append(font.render(f"velocity {round(consists[controlling_consist].velocity*3.6,2)} km/h",True,text_color))
                info_blit_list.append(font.render(f"pressure {round(consists[controlling_consist].pressure)} aT",True,text_color))
                info_blit_list.append(font.render(f"km {consists[controlling_consist].km}",True,text_color))
                info_blit_list.append(font.render(f"tk {consists[controlling_consist].tk}",True,text_color))
                info_blit_list.append(font.render(f"energy {consists[controlling_consist].energy}",True,text_color))
                info_blit_list.append(font.render(f"emf {consists[controlling_consist].electromotive_force}",True,text_color))
                info_blit_list.append(font.render(f"volts {consists[controlling_consist].engine_voltage}",True,text_color))
                info_blit_list.append(font.render(f"current {consists[controlling_consist].engine_current}",True,text_color))
                info_blit_list.append(font.render(f"RP {consists[controlling_consist].control_wires['rp']}",True,text_color))
                info_blit_list.append(font.render(f"vz1 {consists[controlling_consist].vz_1}",True,text_color))
                info_blit_list.append(font.render(f"doors {consists[controlling_consist].doors}",True,text_color))
                info_blit_list.append(font.render(f"traction {consists[controlling_consist].control_wires['traction']}",True,text_color))
                info_blit_list.append(font.render(f"CW doors {consists[controlling_consist].control_wires['left_doors'],consists[controlling_consist].control_wires['right_doors']}",True,text_color))
                if consists[controlling_consist].consist_info["control_system_type"] == "reostat":
                    info_blit_list.append(font.render(f"rk {consists[controlling_consist].rk}",True,text_color))

                if debug > 1:
                    info_blit_list.append(font.render(f"reverser {consists[controlling_consist].controlling_direction}",True,text_color))
                    info_blit_list.append(font.render(f"traction {consists[controlling_consist].traction_direction}",True,text_color))
                    info_blit_list.append(font.render(f"movement {consists[controlling_consist].velocity_direction}",True,text_color))
                

        for i, line in enumerate(info_blit_list):
                screen.blit(line, (0, 20*i))

        if spawn_menu[0] and spawn_menu[1] < 1:
            spawn_menu[1] += clock.get_fps()/60*0.0167
            if spawn_menu[1] > 1: spawn_menu[1] = 1
        elif not spawn_menu[0] and spawn_menu[1] > 0:
            spawn_menu[1] -= clock.get_fps()/60*0.0167
            if spawn_menu[1] < 0: spawn_menu[1] = 0

    elif screen_state == "exit": #техническое состояние для выхода из игры
        working = False
    
    elif screen_state == "sdk_load": #техническое состояние для прогрузки пакетов в SDK
        sdk_params["folder_list"] = []
        pak_folders = os.listdir(os.path.join(current_dir,"paks"))

        for folder in pak_folders:
            folder_contents = os.listdir(os.path.join(current_dir,"paks",folder))
            if "pack.json" in folder_contents:
                sdk_params["folder_list"].append(folder)
        screen_state = "sdk"

    pg.display.update()
    clock.tick(60)
    if not working:
        pg.quit()