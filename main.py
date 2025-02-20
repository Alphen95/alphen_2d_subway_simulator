#ДИСКЛЕЙМЕР - DISCLAIMER
#не пытайтесь разобраться в коде. - do not try to understand the code.
#он написан предельно плохо и не комментирован. - it's written really poorly and not commentated.
#лучше разберите метрострой, он состоятельнее. - you'd be better off dismembering Metrostroi, as it's written better.
#-alphen95 "Альфен Лачертов" - автор всего кода - code author.

import pygame as pg
import os
import json
import math
import time
import logging
import threading
import random
import pathlib
import pprint
from res.train import *
from res import leitmotif

version = "0.7.1 - локализация"
version_id = version.split(" ")[0]
scale = 1
current_dir = ""
#directory deprecated 11-11-24 to work with cxFreeze and be able to use non-packed gamedata

#from train import *
#Train module deprecated and merged with main 11-11-24
#ага, на**здел. вернул обратно, но теперь оно живёт в res/. 24-11-24 

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
volume = 1
hotkeys = {"vz_1":pg.K_n,"rp_return":pg.K_b,"left_doors":pg.K_a,"right_doors":pg.K_d,"close_doors":pg.K_v}
text_color = (200,200,200)
text_black = (25,25,25)
tunnel_nothingness = (30,30,30)
clicked_on_menu_entry = False
pack_name = ""
render_progress = 0
render_log = []
logger = logging.getLogger("aiss")
logging.basicConfig(filename='latest.log', encoding='utf-8', level=logging.DEBUG)

main_font_height = 20
title_font_height = 30

pg.init()
clock = pg.time.Clock()
screen = pg.display.set_mode((0, 0), pg.SRCALPHA)
title_font = pg.font.Font(os.path.join(current_dir,"res","verdana.ttf"),title_font_height)
font = pg.font.Font(os.path.join(current_dir,"res","verdana.ttf"),main_font_height)
annotation_font = pg.font.Font(os.path.join(current_dir,"res","verdana.ttf"),12)
temp_text = font.render("abcdefghijklmnopqrtsuvwxyz",True,(0,0,0))
char_width = temp_text.get_width()/26

screen_size = screen.get_size()
#screen = pg.display.set_mode(screen_size, pg.SRCALPHA)
pg.display.set_caption(f"Alphen's Isometric Subway Simulator v{version_id}")

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

frame_cnt = 0

screen_state = "load_start"
transition_timer = 100
transition_act = "appear"

pack_chooser_params = {"all":[],"disabled":[],"scroll":0,"selected":None}
world_chooser_params = {"paks":[],"worlds":[],"scroll":0,"selected":None}

text_bank = { #здесь должны быть (будут) все тексты (просто строки, подсказки, элементы вагона и т. д.)
    "en":{
        "base":{
            "load":"loading..."
        }
    },
    "ru":{
        "base":{
            "load":"загрузка пакетов..."
        }
    }
}

sdk_params = {
    "folder_list":[],
    "mode":None,
    "editor_mode":None
}

options_params = {
    "locale_scroll":0,
}

base_sdk_params = {
    "selected_menu":-1,
    "mode":"main",
    "editor_mode":None,
    "current_pack":None,
    "folder_pointer":None,
    "folder_scroll":0,
    "worlds_pointer":None,
    "worlds_name":"",
    "worlds_scroll":0,
    "tile_placer_pointer":None,
    "tile_placer_scroll":0,
    "tile_placer_custom":["",""],
    "tiles_pointer":None,
    "tiles_id": -1,
    "tiles_scroll":0,
    "consist_pointer":None,
    "consist_id": -1,
    "consist_scroll":0,
    "element_pointer":None,
    "element_name":"",
    "element_scroll":0,
    "scale":4,
    "editing":False
}

sdk_mode_timers = {
    "consist":0,
    "world":0,
    "tiles":0
}

sdk_editor_mode_timers = {
    "graph_define":0,
    "tracks":0,
    "signals":0
}

sdk_loaded_pack = {"graphics":{},"info":{}}

progress = 0
load_timer = 0
current_tool = -1
current_toolbar = 0
custom_tool_parameters = ["","",0]
spawn_menu = [False, 0, None, None]
toolbar = []

signal_editor_params = {
    "current":None,
    "editor_name":"",
    "linked_blocks":[],
    "next":"",
    "speed":"",
    "scroll":0,
    "active":None
}

pg.mixer.init(44100, -16, 2, 1024)
pg.mixer.set_num_channels(128) #128 каналов. 10 резервированы под спецзвуки. возможно, верну клацанье КМ и добавлю ТК.

channel_dict = {}
roll_channels_occupied = [0,1,2,3,4] #каналы используются парами. резервирую заранее 10 каналов под разные звуки.
ars_beep_channel = pg.mixer.Channel(1) # 1 канал (ОРТ) - пищание АРС

sign = lambda x: math.copysign(1, x)

def text_splitter(base_string, char_width,max_width):
    max_char_per_line = int(max_width/char_width)
    return [base_string[i:i+max_char_per_line] for i in range(0, len(base_string), max_char_per_line)]

def fetch_line(subset, line_definition):
    global selected_locale, text_bank
    line = ""

    if selected_locale in text_bank:
        if subset in text_bank[selected_locale]:
            if line_definition in text_bank[selected_locale][subset]:
                line = text_bank[selected_locale][subset][line_definition]

    return line

def render():
    global pack_name,render_progress,sdk_params,render_log
    sprite_stack_factor = 4
    compression = 2
    world_angle = 45
    train_angles = [world_angle,world_angle+180]+[14+world_angle,-14+world_angle,180-14+world_angle,180+14+world_angle]
    total = 0

    if not os.path.isdir(f"paks/{pack_name}/render"):
        os.makedirs(os.path.join("paks",pack_name,"render"))

    with open(os.path.join("paks",pack_name,"pack.json"),encoding="utf-8") as file:
        pack_parameters = json.loads(file.read())

        temp_sprites = {}
        filenames = os.listdir(os.path.join("paks",pack_name))
        rendered_info = {"tiles":[],"trains":[]}
        
        for filename in filenames:
            if filename[-4:] == ".png":
                temp_sprites[filename[:-4]] = pg.image.load(os.path.join(*(["paks",pack_name,filename])))
        
        if "tiles" in pack_parameters:
            total += len(pack_parameters["tiles"])*5

        if "trains" in pack_parameters:
            for train in pack_parameters["trains"]:
                total += len(train["render_sprite_info"])*len(train_angles)
        sp_value = 100/total
    
        if "tiles" in pack_parameters:
            for info_pack in pack_parameters["tiles"]:
                base_ground_sprite = temp_sprites[info_pack["filename"]].subsurface(info_pack["params"][0],info_pack["params"][1],info_pack["params"][2]*info_pack["params"][4],info_pack["params"][3])
                base_ground_sprite = pg.transform.scale(base_ground_sprite,(base_ground_sprite.get_width()*4,base_ground_sprite.get_height()*4))

                base_layers = []
                
                for i in range(info_pack["params"][4]):
                    x_pos = info_pack["params"][2]*i
                    base_layers.append(
                        pg.transform.flip(
                            #pg.transform.scale(
                                base_ground_sprite.subsurface(
                                    x_pos*4,
                                    0,
                                    info_pack["params"][2]*4,
                                    info_pack["params"][3]*4
                                ),
                                #(info_pack["params"][2]*2,info_pack["params"][3]*2)
                            #),
                            info_pack["params"][6],
                            info_pack["params"][7]
                        )
                    )

                w, h = pg.transform.rotate(
                    base_layers[0],world_angle).get_size()
                h=h/compression
                surface = pg.Surface((w,h+(info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor))
                surface.set_colorkey((0,0,0))

                for i in range(info_pack["params"][4]*sprite_stack_factor):
                    pos = (0,surface.get_height()-i-h-info_pack["params"][5]*sprite_stack_factor)
                    z=base_layers[int(i/sprite_stack_factor)]
                    base_img = pg.transform.rotate(z,world_angle)
                    surface.blit(pg.transform.scale(base_img,(base_img.get_width(),base_img.get_height()/compression)),pos)

                pg.image.save(surface,os.path.join("paks",pack_name,"render",f"{info_pack['name']}_4.png"))
                render_progress+=sp_value

                w, h = pg.transform.rotate(
                    base_layers[0].subsurface(
                        0,
                        base_layers[0].get_height()/4,
                        base_layers[0].get_width(),
                        base_layers[0].get_height()/4
                    ),world_angle).get_size()
                h=h/compression
                    
                for q in range(4):

                    surface = pg.Surface((w,h+(info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor))
                    surface.set_colorkey((0,0,0))

                    for i in range(info_pack["params"][4]*sprite_stack_factor):
                        pos = (0,surface.get_height()-i-h-info_pack["params"][5]*sprite_stack_factor)
                        z=base_layers[int(i/sprite_stack_factor)]
                        base_img = pg.transform.rotate(z.subsurface(0,z.get_height()/4*q,z.get_width(),z.get_height()/4),world_angle)
                        base_img.set_colorkey()
                        surface.blit(pg.transform.scale(base_img,(base_img.get_width(),base_img.get_height()/compression)),pos)

                    pg.image.save(surface,os.path.join("paks",pack_name,"render",f"{info_pack['name']}_{q}.png"))
                    render_progress+=sp_value

                rendered_info["tiles"].append([info_pack['name'],(info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor-1])
                render_log.append(f"Rendered {info_pack['name']} tile")
        if "trains" in pack_parameters:
            for train in pack_parameters["trains"]:
                frame_cnt = 0
                
                train_parameters = train
                key = train_parameters["system_name"]
                    
                sprite_stack_factor = 4
                
                base_train_sprite = pg.image.load(os.path.join(*(["paks",pack_name,train_parameters["sprite"]])))

                for sprite_params in train_parameters["render_sprite_info"]:
                    base_layers = []
                    door_type = sprite_params["type"]

                    for j in range(sprite_params["layers"]):
                        x_pos = sprite_params["w"]*j
                        base_layers.append(pg.transform.scale(base_train_sprite.subsurface(x_pos,sprite_params["y"],sprite_params["w"],sprite_params["h"]),(sprite_params["w"]*4,sprite_params["h"]*4)))


                    for rotation in train_angles:
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
                        pg.image.save(global_l_surface,os.path.join("paks",pack_name,"render",f"{key}_{door_type}_{rotation}_l.png"))
                        pg.image.save(global_r_surface,os.path.join("paks",pack_name,"render",f"{key}_{door_type}_{rotation}_r.png"))
                        render_progress+=sp_value
                        render_log.append(f"Rendered {key} train {door_type} door state, {rotation}°")
                    rendered_info["trains"].append([key,door_type,sprite_params["layers"]*sprite_stack_factor-1,train_parameters["designed_for"],train_parameters["name"]])
    pack_parameters["rendered"] = rendered_info
    with open(os.path.join("paks",pack_name,"pack.json"),encoding="utf-8",mode="w") as file:
        json.dump(pack_parameters, file, ensure_ascii=False, sort_keys=True,indent=4)
    sdk_params["mode"] = "render_complete"

def draw_button(target, text, coords, m_coords, m_state,pos_inverted=False,pos_centered=False):
    text_line = font.render(text,True,text_black) if text not in ["arrow_up","arrow_down","arrow_left","arrow_right"] else pg.Surface((6+main_font_height,6+main_font_height))

    magic_constant = 8

    mod_inverter_w = (magic_constant+text_line.get_width())*(pos_inverted or pos_centered)
    mod_inverter_w = mod_inverter_w / (2 if pos_centered else 1)
    mod = 2 if coords[0]-mod_inverter_w <= m_coords[0] <= coords[0]-mod_inverter_w+magic_constant+text_line.get_width() and  coords[1] <= m_pos[1] <= coords[1]+8+main_font_height and m_state[0] else 0

    pg.draw.rect(target,(20,20,20),(coords[0]+2-mod_inverter_w,coords[1]+2,magic_constant+text_line.get_width(), 6+main_font_height))
    pg.draw.rect(target,(100,100,100),(coords[0]-mod_inverter_w+mod,coords[1]+mod,magic_constant+text_line.get_width(),6+main_font_height))
    #pg.draw.rect(target,(100,100,100),(coords[0]-mod_inverter_w+mod+1,coords[1]+mod+1,magic_constant+text_line.get_width()-2,6+main_font_height-2))
    if text not in ["arrow_up","arrow_down","arrow_left","arrow_right"]:
        target.blit(text_line,(coords[0]-mod_inverter_w+mod+(magic_constant+text_line.get_width())/2-text_line.get_width()/2,
            coords[1]+mod+(6+main_font_height)/2-text_line.get_height()/2))
    else:
        if text == "arrow_up":pg.draw.polygon(screen,text_black,(
                (screen_size[0]/4*3-20-8-main_font_height+6,screen_size[1]/3+8+main_font_height+22),
                (screen_size[0]/4*3-20-8-main_font_height+22,screen_size[1]/3+8+main_font_height+22),
                (screen_size[0]/4*3-20-8-main_font_height+14,screen_size[1]/3+8+main_font_height+6),
            ))
        elif text == "arrow_down":pg.draw.polygon(screen,text_black,(
                (screen_size[0]/4*3-20-8-main_font_height+6,screen_size[1]/3+(8+main_font_height)*(max_lines-2)+6),
                (screen_size[0]/4*3-20-8-main_font_height+22,screen_size[1]/3+(8+main_font_height)*(max_lines-2)+6),
                (screen_size[0]/4*3-20-8-main_font_height+14,screen_size[1]/3+(8+main_font_height)*(max_lines-2)+22),
            ))
    
    return bool(mod)


def sprite_load_routine():
    global ground_sprites, train_sprites,train_types, sounds, consists_info,sprite_loading_info,screen_state,consists,progress,icons,train_repaint_dictionary, misc_sprites,toolbar, config,text_bank,transition_timer,transition_act,frame_cnt,total_frame_cnt,logger
    pak_folders = os.listdir(os.path.join(current_dir,"paks"))
    train_sprites["sprites"] = {}
    train_sprites["controls"] = {}
    toolbar = []
    train_angles = [world_angle,world_angle+180]+[14+world_angle,-14+world_angle,180-14+world_angle,180+14+world_angle]

    for folder in pak_folders:
        folder_contents = os.listdir(os.path.join(current_dir,"paks",folder))
        if "pack.json" in folder_contents and folder not in config["disabled_packs"]:
            logger.info(f"started loading {folder} pack")
            
            with open(os.path.join(current_dir,"paks",folder,"pack.json"),encoding="utf-8") as file:
                pack_parameters = json.loads(file.read())

                temp_sprites = {}
                filenames = os.listdir(os.path.join(current_dir,"paks",folder))
                for filename in filenames:
                    if filename[-4:] == ".png":
                        temp_sprites[filename[:-4]] = pg.image.load(os.path.join(*([current_dir,"paks",folder,filename])))
                        #temp_sprites[filename[:-4]]

                if "editor_tiles" in pack_parameters:
                    toolbar+=pack_parameters["editor_tiles"]

                if "locale" in pack_parameters:
                    for lang in pack_parameters["locale"]:
                        if lang not in text_bank: text_bank[lang] = {}
                        for subset in pack_parameters["locale"][lang]:
                            if subset not in text_bank[lang]: text_bank[lang][subset] = {}
                            for line in pack_parameters["locale"][lang][subset]:
                                text_bank[lang][subset][line] = pack_parameters["locale"][lang][subset][line]

                if "rendered" in pack_parameters:
                    for rtile_i in pack_parameters["rendered"]["tiles"]:
                        rtile = rtile_i[0]
                        ground_sprites[rtile] = {}
                        for q in range(4):
                            ground_sprites[rtile][q] = pg.image.load(os.path.join(*(["paks",folder,"render",f"{rtile}_{q}.png"])))
                            ground_sprites[rtile][q].set_colorkey((0,0,0))
                        ground_sprites[rtile]["height"] = rtile_i[1]
                        ground_sprites[rtile][world_angle] = pg.image.load(os.path.join(*(["paks",folder,"render",f"{rtile}_4.png"])))
                        ground_sprites[rtile][world_angle].set_colorkey((0,0,0))
                        logger.info(f"loaded prerendered {rtile} tile")

                    for rtrain_i in pack_parameters["rendered"]["trains"]:
                        train_name, train_key = rtrain_i[0], rtrain_i[1]
                        if train_name not in train_sprites["sprites"]:
                            train_sprites["sprites"][train_name] = {}
                            train_sprites["sprites"][train_name]["name"] = rtrain_i[4]
                            if rtrain_i[3] in train_repaint_dictionary:
                                train_repaint_dictionary[rtrain_i[3]].append(train_name)
                            else:
                                train_repaint_dictionary[rtrain_i[3]] = [train_name]
                        train_sprites["sprites"][train_name][train_key] = {}
                        
                        for rotation in train_angles:
                            train_sprites["sprites"][train_name][train_key][rotation] = {}
                            train_sprites["sprites"][train_name][train_key][rotation]["l"] = pg.image.load(os.path.join(*(["paks",folder,"render",f"{train_name}_{train_key}_{rotation}_l.png"])))
                            train_sprites["sprites"][train_name][train_key][rotation]["l"].set_colorkey((0,0,0))
                            train_sprites["sprites"][train_name][train_key][rotation]["r"] = pg.image.load(os.path.join(*(["paks",folder,"render",f"{train_name}_{train_key}_{rotation}_r.png"])))
                            train_sprites["sprites"][train_name][train_key][rotation]["r"].set_colorkey((0,0,0))
                        train_sprites["sprites"][train_name][train_key]["height"] = rtrain_i[2]
                        logger.info(f"loaded prerendered {train_name} train type, {train_key} door type")
                        

                if "tiles" in pack_parameters:
                    for info_pack in pack_parameters["tiles"]:
                        frame_cnt = 0
                        if info_pack["name"] not in ground_sprites:
                            sprite_stack_factor = 4

                            base_ground_sprite = temp_sprites[info_pack["filename"]].subsurface(info_pack["params"][0],info_pack["params"][1],info_pack["params"][2]*info_pack["params"][4],info_pack["params"][3])
                            base_ground_sprite.set_colorkey((0,0,0))
                            base_ground_sprite = pg.transform.scale(base_ground_sprite,(base_ground_sprite.get_width()*4,base_ground_sprite.get_height()*4))

                    
                            base_layers = []
                            
                            for i in range(info_pack["params"][4]):
                                x_pos = info_pack["params"][2]*i
                                base_layers.append(
                                    pg.transform.flip(
                                        #pg.transform.scale(
                                            base_ground_sprite.subsurface(
                                                x_pos*4,
                                                0,
                                                info_pack["params"][2]*4,
                                                info_pack["params"][3]*4
                                            ),
                                            #(info_pack["params"][2]*2,info_pack["params"][3]*2)
                                        #),
                                        info_pack["params"][6],
                                        info_pack["params"][7]
                                    )
                                )

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
                                #surface.set_colorkey((0,0,0))

                                for i in range(info_pack["params"][4]*sprite_stack_factor):
                                    pos = (0,surface.get_height()-i-h-info_pack["params"][5]*sprite_stack_factor)
                                    z=base_layers[int(i/sprite_stack_factor)]
                                    base_img = pg.transform.rotate(z.subsurface(0,z.get_height()/4*q,z.get_width(),z.get_height()/4),rotation)
                                    surface.blit(pg.transform.scale(base_img,(base_img.get_width(),base_img.get_height()/compression)),pos)
                                ground_sprites[info_pack["name"]][q] = surface
                                progress+=1
                            ground_sprites[info_pack["name"]]["height"] = (info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor-1

                            logger.info(f"rendered {info_pack['name']} tile, took {frame_cnt} frames")
                
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
                        consists_info[key] = train_parameters["consist_info"]
                        sprite_stack_factor = 4
                        train_sprites["controls"][key] = {}

                        controls_info = train_parameters["control_panel_info"]
                        for control in controls_info:
                            train_sprites["controls"][key][control] = pg.transform.scale(
                                base_control_panel_sprite.subsurface(controls_info[control]["x"],controls_info[control]["y"],controls_info[control]["w"],controls_info[control]["h"]),
                                (controls_info[control]["w"]*controls_info[control]["scale"],controls_info[control]["h"]*controls_info[control]["scale"]))

                        train_types[key] = {}
                        train_types[key]["size"] = train_parameters["clickable_size"]
                        #train_types[key]["name"] = train_parameters["name"]

                        sounds[key] = {}
                        for sound in train_parameters["sound_loading_info"]:
                            sounds[key][sound] = pg.mixer.Sound(os.path.join(current_dir,"paks",folder,train_parameters["sound_loading_info"][sound]))
                            sounds[key][sound].set_volume(volume)
                            
                        logger.info(f"loaded {key} consist")
                if "trains" in pack_parameters:
                    for train in pack_parameters["trains"]:
                        frame_cnt = 0
                        
                        train_parameters = train
                        key = train_parameters["system_name"]
                        if key not in train_sprites["sprites"]:
                            train_sprites["sprites"][key] = {}
                            if train_parameters["designed_for"] in train_repaint_dictionary:
                                train_repaint_dictionary[train_parameters["designed_for"]].append(key)
                            else:
                                train_repaint_dictionary[train_parameters["designed_for"]] = [key]
                                
                            train_sprites["sprites"][key]["name"] = train_parameters["name"]
                            sprite_stack_factor = 4
                            
                            base_train_sprite = pg.image.load(os.path.join(*([current_dir,"paks",folder,train_parameters["sprite"]]))).convert_alpha()

                            for sprite_params in train_parameters["render_sprite_info"]:
                                base_layers = []
                                door_type = sprite_params["type"]
                                train_sprites["sprites"][key][door_type] = {"type":door_type}

                                for j in range(sprite_params["layers"]):
                                    x_pos = sprite_params["w"]*j# if not ("reversed" in sprite_params and sprite_params["reversed"]) else sprite_params["h_layer"]*(sprite_params["layer_amount"]-1-i)
                                    base_layers.append(pg.transform.scale(base_train_sprite.subsurface(x_pos,sprite_params["y"],sprite_params["w"],sprite_params["h"]),(sprite_params["w"]*4,sprite_params["h"]*4)))


                                for rotation in train_angles:
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
                                        #l_surface.set_colorkey((0,0,0))
                                        #r_surface.set_colorkey((0,0,0))

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

                            logger.info(f"rendered {key} repaint, took {frame_cnt} frames")
                        
        progress+=1

    transition_timer = 100-transition_timer
    transition_act = "disappear:title"
    logger.info(f"total: {total_frame_cnt} frames (roughly {total_frame_cnt/60} seconds)")
    
total_frame_cnt = 0
world = {}
signals = {}
switches = {}

#trains = {}

pack_render_thread = threading.Thread(target=render)

player_pos = [256*0.5,1024*0.5]
m_btn = [0,0,0]
world_mouse_coord = [0,0]
mouse_block_pos = (None,None)
mouse_clicked = False
mouse_released = False
line_pos = 0

while working:
    keydowns = []
    keyups = []
    unicode = {"chars":"","return":False,"backspace":False,"escape":False}
    mouse_clicked_prev = mouse_clicked
    mouse_clicked = False
    mouse_released = False
    for evt in pg.event.get():
        if evt.type == pg.QUIT:
            working = False
        if evt.type == pg.KEYDOWN:
            keydowns.append(evt.key)

            if 32 <= evt.key%1000 <= 64 or evt.key in [1073,1078] or 91 <= evt.key%1000 <= 122:unicode["chars"]+=evt.unicode
            elif evt.key == pg.K_RETURN: unicode["return"] = True
            elif evt.key == pg.K_BACKSPACE: unicode["backspace"] = True
            elif evt.key == pg.K_ESCAPE: unicode["escape"] = True

            if evt.key == pg.K_q and screen_state == "playing":
                debug = (debug+1)%3
            
            if screen_state == "editor" and custom_tool_parameters[2] != 0:
                if evt.key == pg.K_BACKSPACE:
                    custom_tool_parameters[custom_tool_parameters[2]-1] = custom_tool_parameters[custom_tool_parameters[2]-1][:-1]
                else:
                    custom_tool_parameters[custom_tool_parameters[2]-1] += evt.unicode
        if evt.type == pg.KEYUP:
            keyups.append(evt.key)
        if evt.type == pg.MOUSEBUTTONDOWN and not m_btn[0] and not m_btn[2]:
            mouse_clicked = True
        elif evt.type == pg.MOUSEBUTTONUP:
            mouse_released = True
    if screen_state == "loading":
        screen.fill(tunnel_nothingness)
        opacity = (100-transition_timer if transition_act in ["appear",""] else transition_timer)
        if opacity != 100:
            opaque_surf = pg.Surface(screen_size)
        else:
            opaque_surf = screen
        text_color = (200,200,200)
        opaque_surf.fill(tunnel_nothingness)
        text = font.render(fetch_line("base","load"), True, text_color)
        opaque_surf.blit(text,(screen_size[0]/2-text.get_width()/2, screen_size[1]/2-text.get_height()))
        line_pos = (line_pos + 2) % 280
        thingy_color = (128,255,0) if sprite_thread.is_alive() or transition_timer else (204,20,20)
        pg.draw.rect(opaque_surf,thingy_color,((screen_size[0]/2-124+line_pos) if 0 < line_pos < 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
        pg.draw.rect(opaque_surf,thingy_color,((screen_size[0]/2-124+line_pos-6) if 0 < line_pos-6< 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
        pg.draw.rect(opaque_surf,thingy_color,((screen_size[0]/2-124+line_pos-12) if 0 < line_pos-12 < 246 else -100,screen_size[1]/2+2,2,text.get_height()-6))
        pg.draw.rect(opaque_surf,(255,255,255),(screen_size[0]/2-124,screen_size[1]/2+2,248,text.get_height()-4),2)
        if opacity != 100:
            opaque_surf.convert()
            opaque_surf.set_alpha(255*(opacity/100))
            screen.blit(opaque_surf,(0,0))

    elif screen_state == "title":
        animation = (100-100*((transition_timer/100)**2) if transition_act in ["appear",""] else 100*((transition_timer/100)**2))
        pressed = pg.key.get_pressed()
        m_pos = pg.mouse.get_pos()
        m_btn = pg.mouse.get_pressed()
        
        text_color = (200,200,200)
        screen.fill(tunnel_nothingness)
        #text = font.render(f"Alphen's Isometric Subway Simulator v{version_id}", True, text_color)
        #screen.blit(text,(screen_size[0]/2-text.get_width()/2, screen_size[1]/2-2*text.get_height()))
        
        icon_ht_modif = -misc_sprites["game_icon"].get_height()*1.5*(100-animation)/100
        #print(animation,icon_ht_modif)
        screen.blit(
            pg.transform.scale(
                misc_sprites["game_icon"],(
                misc_sprites["game_icon"].get_width(),
                misc_sprites["game_icon"].get_height()
            )),(
                36,
                36+icon_ht_modif
            ))
        text = font.render("alphen's isometric", True, text_black)
        screen.blit(text,(36+128+20,36+64-text.get_height()-2+icon_ht_modif))
        text = font.render("subway simulator", True, text_black)
        screen.blit(text,(36+128+20,36+64+2+icon_ht_modif))

        text_lines = [
            [font.render(fetch_line("base","new_game"),True,text_color),"world_chooser_open"],
            None,
            [font.render(fetch_line("base","pack_editor"),True,text_color),"sdk_load"],
            None,
            [font.render(fetch_line("base","pack_selector"),True,text_color),"pack_chooser_open"],
            [font.render(fetch_line("base","settings"),True,text_color),"options"],
            None,
            None,
            [font.render(fetch_line("base","quit"),True,text_color),"exit"]
        ]

        max_w = 0

        for z in text_lines:
            if z!= None and z[0].get_width() > max_w: max_w = z[0].get_width()

        text_w_modif = -max_w*2*(100-animation)/100

        for i,line in enumerate(text_lines):
            if line != None:
                screen.blit(line[0],(64+text_w_modif,36+128+20+(main_font_height+4)*i))
                if line[1] != None and m_btn[0] and load_timer <= 200:
                    if (64+text_w_modif <= m_pos[0] <= 64+line[0].get_width()+text_w_modif and 
                    36+128+20+(main_font_height+4)*i <= m_pos[1] <= 36+128+20+(main_font_height+4)*(i+1)) and transition_timer == 0:
                        player_pos = [0,0]
                        transition_act = f"disappear:{line[1]}"
                        transition_timer = 100-transition_timer

    elif screen_state == "world_chooser":
        animation = (100-100*((transition_timer/100)**2) if transition_act in ["appear",""] else 100*(1-(1-transition_timer/100)**2))

        screen.fill(tunnel_nothingness)
        chrect = (screen_size[0]/16+screen_size[0]*(1-animation/100),screen_size[1]/12,screen_size[0]/8*7,screen_size[1]/6*5)
        line_height = 28
        max_lines = int((chrect[3]-8)/line_height)
        hmargin = (chrect[3]-line_height*max_lines)/2
        bwidth = (chrect[2]-16-4*3)/4
        
        pressed = pg.key.get_pressed()
        m_pos = pg.mouse.get_pos()
        m_btn = pg.mouse.get_pressed()

        leitmotif.draw_window(screen,chrect)
        leitmotif.draw_label(screen,(chrect[0]+8,chrect[1]+hmargin,chrect[2]-16,line_height),"center",fetch_line("base","world_chooser"),font)

        items = world_chooser_params["worlds"]
        mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

        act = leitmotif.draw_itemlist(screen,(chrect[0]+8,chrect[1]+hmargin+line_height*1.5,chrect[2]-16,0),items,max_lines-3,world_chooser_params["scroll"],world_chooser_params["selected"],font,line_height,mouse_state)

        if act != None:
            if act[0] == "select": 
                world_chooser_params["selected"] = act[1]

                #sdk_params["consist_id"] = world_items.index(act[1])
            elif act[0] == "scroll_down" and len(items)-world_chooser_params["scroll"]-max_lines+3 > 0: world_chooser_params["scroll"]+=1
            elif act[0] == "scroll_up" and world_chooser_params["scroll"] > 0: world_chooser_params["scroll"]-=1

        act = leitmotif.draw_button(screen,(chrect[0]+chrect[2]/2-bwidth/2,chrect[1]+hmargin+line_height*(max_lines-1),bwidth,line_height),"center",fetch_line("base","play"),font,mouse_state)

        if act != None and world_chooser_params["selected"] != None and ("disappear" not in transition_act or transition_act == None): 
            transition_timer = 100-transition_timer
            transition_act = "disappear:play_load"
            world_pack = world_chooser_params["paks"][world_chooser_params["worlds"].index(world_chooser_params["selected"])]
            world_name = world_chooser_params["selected"]

        if pressed[pg.K_ESCAPE] and (transition_act == None or "disappear" not in transition_act): 
            transition_timer = 100-transition_timer
            transition_act = "disappear:title"

    elif screen_state == "pack_chooser":
        animation = (100-100*((transition_timer/100)**2) if transition_act in ["appear",""] else 100*((transition_timer/100)**2))
        screen.fill(tunnel_nothingness)
        chrect = (screen_size[0]/16+screen_size[0]*(1-animation/100),screen_size[1]/12,screen_size[0]/8*7,screen_size[1]/6*5)
        line_height = 28
        max_lines = int((chrect[3]-8)/line_height)
        hmargin = (chrect[3]-line_height*max_lines)/2
        bwidth = (chrect[2]-16-4*5)/6
        
        pressed = pg.key.get_pressed()
        m_pos = pg.mouse.get_pos()
        m_btn = pg.mouse.get_pressed()

        leitmotif.draw_window(screen,chrect)
        leitmotif.draw_label(screen,(chrect[0]+8,chrect[1]+hmargin,chrect[2]-16,line_height),"center",fetch_line("base","pack_chooser"),font)

        items = [f"[{'_' if item in pack_chooser_params['disabled'] else 'X'}] {item}" for item in pack_chooser_params["all"]]
        mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

        act = leitmotif.draw_itemlist(screen,(chrect[0]+8,chrect[1]+hmargin+line_height*1.5,chrect[2]-16,0),items,max_lines-3,pack_chooser_params["scroll"],pack_chooser_params["selected"],font,line_height,mouse_state)

        if act != None:
            if act[0] == "select": 
                pack_chooser_params["selected"] = act[1]

                #sdk_params["consist_id"] = world_items.index(act[1])
            elif act[0] == "scroll_down" and len(items)-pack_chooser_params["scroll"]-max_lines+3 > 0: pack_chooser_params["scroll"]+=1
            elif act[0] == "scroll_up" and pack_chooser_params["scroll"] > 0: pack_chooser_params["scroll"]-=1

        act = leitmotif.draw_button(screen,(chrect[0]+8,chrect[1]+hmargin+line_height*(max_lines-1),bwidth,line_height),"center",fetch_line("base","pack_enable"),font,mouse_state)

        if act != None and pack_chooser_params["selected"] != None:
            if pack_chooser_params["selected"][4:] in pack_chooser_params['disabled']:
                pack_chooser_params["disabled"].remove(pack_chooser_params["selected"][4:])
                pack_chooser_params["selected"] = None

                with open("config.json") as f:
                    tmp = json.loads(f.read())

                tmp["disabled_packs"] = pack_chooser_params["disabled"]

                with open("config.json","w") as f:
                    json.dump(tmp, f, ensure_ascii=False, sort_keys=True,indent=4)


        act = leitmotif.draw_button(screen,(chrect[0]+chrect[2]-8-bwidth,chrect[1]+hmargin+line_height*(max_lines-1),bwidth,line_height),"center",fetch_line("base","pack_disable"),font,mouse_state)

        if act != None and pack_chooser_params["selected"] != None:
            if pack_chooser_params["selected"][4:] not in pack_chooser_params['disabled']:
                pack_chooser_params["disabled"].append(pack_chooser_params["selected"][4:])
                pack_chooser_params["selected"] = None

                with open("config.json") as f:
                    tmp = json.loads(f.read())

                tmp["disabled_packs"] = pack_chooser_params["disabled"]

                with open("config.json","w") as f:
                    json.dump(tmp, f, ensure_ascii=False, sort_keys=True,indent=4)

        if pressed[pg.K_ESCAPE] and "disappear" not in transition_act:  
            if pack_chooser_params["disabled"] == config["disabled_packs"]:
                transition_timer = 100-transition_timer
                transition_act = "disappear:title"
            else:
                transition_timer = 100-transition_timer
                transition_act = "disappear:load_start"

    elif screen_state == "options":
        animation = (100-100*((transition_timer/100)**2) if transition_act in ["appear",""] else 100*((transition_timer/100)**2))
        screen.fill(tunnel_nothingness)
        chrect = (screen_size[0]/16+screen_size[0]*(1-animation/100),screen_size[1]/12,screen_size[0]/8*7,screen_size[1]/6*5)
        line_height = 28
        max_lines = int((chrect[3]-8)/line_height)
        hmargin = (chrect[3]-line_height*max_lines)/2
        bwidth = (chrect[2]-16-4*5)/6
        
        pressed = pg.key.get_pressed()
        m_pos = pg.mouse.get_pos()
        m_btn = pg.mouse.get_pressed()

        leitmotif.draw_window(screen,chrect)
        leitmotif.draw_label(screen,(chrect[0]+8,chrect[1]+hmargin,chrect[2]-16,line_height),"center",fetch_line("base","settings"),font)

        items = [lang for lang in text_bank]
        mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

        leitmotif.draw_label(screen,(chrect[0]+chrect[2]/2+4,chrect[1]+hmargin+(max_lines/2-3.5)*line_height,chrect[2]/2-12,line_height),"center",fetch_line("base","locale"),font)
        act = leitmotif.draw_itemlist(screen,(chrect[0]+chrect[2]/2,chrect[1]+hmargin+(max_lines/2-2.5)*line_height,chrect[2]/2-8,0),items,4,options_params["locale_scroll"],selected_locale,font,line_height,mouse_state)

        if act != None:
            if act[0] == "select": 
                selected_locale= act[1]

                #sdk_params["consist_id"] = world_items.index(act[1])
            elif act[0] == "scroll_down" and len(items)-options_params["locale_scroll"]-4 > 0: options_params["locale_scroll"]+=1
            elif act[0] == "scroll_up" and options_params["locale_scroll"] > 0: options_params["locale_scroll"]-=1

        leitmotif.draw_label(screen,(chrect[0]+8,chrect[1]+hmargin+(max_lines/2-1)*line_height,chrect[2]/2-12,line_height),"center",fetch_line("base","volume")+f": {int(round(volume*100,0))}%",font)
        volume = leitmotif.draw_slider(screen,(
            chrect[0]+8+32,
            chrect[1]+hmargin+(max_lines/2)*line_height,
            chrect[2]/2-12-64,line_height),volume,mouse_state)

        if pressed[pg.K_ESCAPE] and "disappear" not in transition_act:  
            transition_timer = 100-transition_timer
            transition_act = "disappear:title"

            with open("config.json", encoding="utf-8") as f:
                config = json.loads(f.read())
            
            config["volume"] = volume
            config["selected_locale"] = selected_locale

            
            with open("config.json", encoding="utf-8", mode="w") as f:
                json.dump(config, f, ensure_ascii=False, sort_keys=True,indent=4)

    elif screen_state == "sdk":
        animation = (100*((transition_timer/100)**2) if transition_act in ["appear",""] else 100-100*((transition_timer/100)**2))
        screen.fill(tunnel_nothingness)
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
        editor_block_size = (128,512)
        iconbar_height = 140
        iconbar_size = (64,128)
        textbox_length = 280

        if sdk_params["editor_mode"] == "graph_define":
            if "panel" in sdk_loaded_pack["graphics"]:
                screen.blit(pg.transform.scale(sdk_loaded_pack["graphics"]["panel"],
                        (sdk_loaded_pack["graphics"]["panel"].get_width()*sdk_params["scale"],sdk_loaded_pack["graphics"]["panel"].get_height()*sdk_params["scale"])),
                    (screen_size[0]/2-sdk_loaded_pack["graphics"]["panel"].get_width()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][0],
                    screen_size[1]/2-sdk_loaded_pack["graphics"]["panel"].get_height()*sdk_params["scale"]/2+sdk_loaded_pack["pos"][1])
                    )
                if sdk_params["element_pointer"] != -1:
                    param = sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][sdk_params["element_pointer"]]
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

        elif sdk_params["mode"] == "world" and sdk_params["worlds_pointer"] != None:
            block_pos = [int((player_pos[0]-(editor_block_size[0] if player_pos[0] < 0 else 0))/editor_block_size[0]),
                        int((player_pos[1]-(editor_block_size[1] if player_pos[1] < 0 else 0))/editor_block_size[1])]
            
            for block_x in range(-1-int(screen_size[0]/editor_block_size[0]),int(screen_size[0]/editor_block_size[0])+2):
                for block_y in range(-1-int(screen_size[1]/editor_block_size[1]),int(screen_size[1]/editor_block_size[1])+2):
                    tile_world_position = f"{block_pos[0]+block_x}:{block_pos[1]+block_y}"

                    pg.draw.rect(screen,(30,30,30),
                        (screen_size[0]/2+block_x*editor_block_size[0]-player_pos[0]%editor_block_size[0],
                        screen_size[1]/2+block_y*editor_block_size[1]-player_pos[1]%editor_block_size[1],
                        editor_block_size[0],
                        editor_block_size[1]
                        ),4        
                    )

                    if tile_world_position in sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["world"]:
                        watp = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["world"][tile_world_position][0]
                        
                        if watp in icons:
                            screen.blit(pg.transform.scale(icons[watp],editor_block_size
                                    ),(
                                    screen_size[0]/2+block_x*editor_block_size[0]-player_pos[0]%editor_block_size[0],
                                    screen_size[1]/2+block_y*editor_block_size[1]-player_pos[1]%editor_block_size[1])
                                )
                        else:
                            icon = None
                            text = None
                            if watp[-8:] == "platform": 
                                icon = "generic_st_platform"
                                text = watp[:-8]
                            elif watp[-10:] == "platform_f": 
                                icon = "generic_st_platform_f"
                                text = watp[:-10]
                            elif watp[-10:] == "track_tstr": 
                                icon = "generic_st_track"
                                text = watp[:-10]
                            elif watp[-12:] == "track_f_tstr": 
                                icon = "generic_st_track_f"
                                text = watp[:-12]
                            elif watp[-4:] == "tstr": icon = "default_tstr"
                            elif watp[-4:] == "tca1": icon = "default_tca1"
                            elif watp[-4:] == "tca2": icon = "default_tca2"
                            elif watp[-4:] == "tcb1": icon = "default_tcb1"
                            elif watp[-4:] == "tcb2": icon = "default_tcb2"
                            elif watp[-4:] == "tsa1": icon = "default_tsa1"
                            elif watp[-4:] == "tsa2": icon = "default_tsa2"
                            elif watp[-4:] == "tsb1": icon = "default_tsb1"
                            elif watp[-4:] == "tsb2": icon = "default_tsb2"
                            elif watp[-4:] == "tsx1": icon = "default_tsx1"
                            elif watp[-4:] == "tsx2": icon = "default_tsx2"
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

                    if sdk_params["editor_mode"] == "signals" and signal_editor_params["current"] != None:
                        if [block_pos[0]+block_x,block_pos[1]+block_y] in signals[signal_editor_params["current"]]["tiles"]:
                            pg.draw.rect(screen,(255,0,0),
                                (screen_size[0]/2+block_x*editor_block_size[0]-player_pos[0]%editor_block_size[0],
                                screen_size[1]/2+block_y*editor_block_size[1]-player_pos[1]%editor_block_size[1],
                                editor_block_size[0],
                                editor_block_size[1]
                            ),4)


        #менюшка наверху экрана
        chars = 0
        action = None
        menu_bar_ht = 0-32*(animation)/100
        menu_text_margin = 30
        menu_text_base_offset = 15
        menu_bar_vert_offset_top = 4
        menu_bar_vert_offset_bottom = 6
        clicked_on_menu_entry = False
        disabled = [
            False,
            sdk_loaded_pack["info"] == {},
            sdk_loaded_pack["info"] == {},
            sdk_params["mode"] != "world" or sdk_params["worlds_pointer"] == None,
            sdk_params["mode"] != "consist" or sdk_params["consist_id"] == -1, 
            False
        ]
        menu_entries = [
            fetch_line("base","editor_file"),
            fetch_line("base","editor_pack"),
            fetch_line("base","editor_mode"),
            fetch_line("base","editor_world"),
            fetch_line("base","editor_consist"),
            fetch_line("base","editor_help"),
        ]
        submenus = [
            [ #меню файла
                (fetch_line("base","editor_open"),"open"),
                (fetch_line("base","editor_save"),"save"),
                (fetch_line("base","editor_close"),"close"),
                (fetch_line("base","editor_exit"),"exit")
            ], [
                (fetch_line("base","editor_render"),"render")
            ], [ #меню режима
                (fetch_line("base","editor_consist_mode"),"editor_consists"),
                (fetch_line("base","editor_repaint_mode"),"editor_trains"),
                (fetch_line("base","editor_tile_mode"),"editor_tiles"),
                (fetch_line("base","editor_map_mode"),"editor_world")
            ], [ #меню редакторов мира
                (fetch_line("base","editor_map_tiles"),"editor_track"),
                (fetch_line("base","editor_map_signalling"),"editor_signal")
            ], [ #меню редакторов состава
                (fetch_line("base","editor_consist_props"),"editor_phys"),
                (fetch_line("base","editor_consist_panel"),"editor_graph"),
                (fetch_line("base","editor_consist_locator"),"editor_graph_define")
            ], [ #меню помощи
                (fetch_line("base","editor_handbook"),None)
            ] 
        ]
        
        pg.draw.rect(screen,(160,160,160),(0,menu_bar_ht,screen_size[0],main_font_height+menu_bar_vert_offset_top+menu_bar_vert_offset_bottom-1))
        pg.draw.rect(screen,(5,5,5),(0,main_font_height+menu_bar_ht+menu_bar_vert_offset_top+menu_bar_vert_offset_bottom-2,screen_size[0],2))
        for enum,entry in enumerate(menu_entries):
            text_line = font.render(entry,True,text_black)
            if disabled[enum]:
                pg.draw.rect(screen,(120,120,120),(
                    menu_text_base_offset+chars-menu_text_margin//2,0,
                    text_line.get_width()+menu_text_margin,main_font_height+8+menu_bar_ht))
            if sdk_params["selected_menu"] == enum:
                pg.draw.rect(screen,(200,200,200),(
                    menu_text_base_offset+chars-menu_text_margin//2,0,
                    text_line.get_width()+menu_text_margin,main_font_height+8+menu_bar_ht))
                pg.draw.rect(screen,(5,5,5),(
                    menu_text_base_offset+chars-menu_text_margin//2,
                    main_font_height+menu_bar_vert_offset_top+menu_bar_vert_offset_bottom+menu_bar_ht,
                    max([font.render(z[0],True,(0,0,0)).get_width() for z in submenus[sdk_params["selected_menu"]]])+menu_text_margin,
                    len(submenus[sdk_params["selected_menu"]])*(8+main_font_height)+2
                ))
                pg.draw.rect(screen,(200,200,200),(
                    menu_text_base_offset+chars-menu_text_margin//2+2,
                    main_font_height+menu_bar_vert_offset_top+menu_bar_vert_offset_bottom+menu_bar_ht,
                    max([font.render(z[0],True,(0,0,0)).get_width() for z in submenus[sdk_params["selected_menu"]]])+menu_text_margin-4,
                    len(submenus[sdk_params["selected_menu"]])*(8+main_font_height)
                ))

                for senum, subentry in enumerate(submenus[sdk_params["selected_menu"]]):
                    subtext_line = font.render(subentry[0],True,text_black)
                    screen.blit(subtext_line,(
                        menu_text_base_offset+chars,
                        main_font_height+menu_bar_ht+menu_bar_vert_offset_top+menu_bar_vert_offset_bottom+2+senum*(8+main_font_height)))
                    
                    tmp1 = main_font_height+menu_bar_ht+menu_bar_vert_offset_top+menu_bar_vert_offset_bottom+2+senum*(8+main_font_height)

                    if (menu_text_base_offset+chars-menu_text_margin//2 <= m_pos[0] <= menu_text_base_offset+chars+text_line.get_width()+menu_text_margin//2 
                        and tmp1 <= m_pos[1] <= tmp1+8+main_font_height) and m_btn[0]: 
                        sdk_params["selected_menu"] = -1
                        action = subentry[1]
                        clicked_on_menu_entry = True

            screen.blit(text_line,(menu_text_base_offset+chars,menu_bar_vert_offset_top+menu_bar_ht))

            if (menu_text_base_offset+chars-menu_text_margin//2 <= m_pos[0] <= menu_text_base_offset+chars+text_line.get_width()+menu_text_margin//2 
                and 0+menu_bar_ht <= m_pos[1] <= main_font_height+8+menu_bar_ht) and m_btn[0] and not disabled[enum]: 
                clicked_on_menu_entry = True
                sdk_params["selected_menu"] = enum
            
            chars+=text_line.get_width()+menu_text_margin

        if m_btn[0] and not clicked_on_menu_entry: sdk_params["selected_menu"] = -1

        if sdk_params["editor_mode"] == "graph_define" and not clicked_on_menu_entry:
            if pg.K_EQUALS in keydowns and not sdk_params["editing"]:
                sdk_params["scale"]+=1
            elif pg.K_MINUS in keydowns and not sdk_params["editing"] and sdk_params["scale"] > 1:
                sdk_params["scale"]-=1

            if m_btn[1]:
                sdk_loaded_pack["pos"][0] += m_pos [0] - old_m_pos[0]
                sdk_loaded_pack["pos"][1] += m_pos [1] - old_m_pos[1]

            if (m_btn[0] or m_btn[2]) and m_pos[0] < screen_size[0]/4*3-20 and mouse_clicked:
                if "panel" in sdk_loaded_pack["graphics"] and sdk_params["element_pointer"] != -1:
                    param = sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][sdk_params["element_pointer"]]
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
                    sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][sdk_params["element_pointer"]]["x"] = x1
                    sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][sdk_params["element_pointer"]]["y"] = y1
                    sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][sdk_params["element_pointer"]]["w"] = x2-x1
                    sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][sdk_params["element_pointer"]]["h"] = y2-y1

        #дешифратор действия
        if action == "open": #диалог открытия пака
            sdk_params["mode"] = "open"
            sdk_params["editor_mode"] = None
            sdk_params["folder_scroll_pointer"] = 0
            
        if action == "render": # диалог пререндера
            sdk_params["mode"] = "render"

        elif action == "save" and sdk_params["folder_pointer"] != None and sdk_params["mode"] != "open" and sdk_loaded_pack["info"] != {}:
            pack_parameters= sdk_loaded_pack["info"]

            with open(os.path.join(current_dir,"paks",sdk_params["folder_pointer"],"pack.json"),"w",encoding="utf-8") as file:
                json.dump(pack_parameters, file, ensure_ascii=False, sort_keys=True,indent=4)

        elif action == "close": #закрыть пак
            for param in base_sdk_params: sdk_params[param] =  base_sdk_params[param]
            sdk_loaded_pack = {"graphics":{},"info":{}}
            sdk_params["mode"] = "main"
            sdk_params["editor_mode"] = None

        elif action == "exit" and "disappear" not in transition_act: #выйти из редактора
            transition_act = "disappear:title"
            transition_timer = 100-transition_timer
            for param in base_sdk_params: sdk_params[param] =  base_sdk_params[param]
            sdk_params["mode"] = "main"
            sdk_params["editor_mode"] = None
            sdk_loaded_pack = {"graphics":{},"info":{}}

        elif action == "editor_consists" and "consists" in sdk_loaded_pack["info"]: #категория редакторов консистов
            sdk_params["mode"] = "consist"
        
        elif action == "editor_world" and "worlds" in sdk_loaded_pack["info"]: #категория редакторов карт
            sdk_params["mode"] = "world"

        elif action == "editor_tiles" and "tiles" in sdk_loaded_pack["info"]: #категория редакторов карт
            sdk_params["mode"] = "tiles"

        elif action == "editor_graph_define": #селектор графики для панели управления
            sdk_params["editor_mode"] = "graph_define"

        elif action == "editor_track": #селектор графики для панели управления
            sdk_params["editor_mode"] = "tracks"
            
        elif action == "editor_signal": #селектор графики для панели управления
            sdk_params["editor_mode"] = "signals"

        line_height = 8+main_font_height

        #диалоговое окно открытия пака
        if sdk_params["mode"] == "open": 
            opener_rect = (screen_size[0]/4-2,screen_size[1]/3-2,screen_size[0]/2+4,screen_size[1]/3+4)
            max_lines = int(opener_rect[3]//line_height)
            height_margin = opener_rect[1]+(opener_rect[3]-line_height*max_lines)/2
            btn_width = (opener_rect[2]-8)/3

            leitmotif.draw_window(screen,opener_rect)

            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

            leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin,opener_rect[2]-16,line_height),"center",fetch_line("base","editor_open_long"),font)

            act = leitmotif.draw_itemlist(screen, (opener_rect[0]+8,height_margin+line_height,opener_rect[2]-16,0),sdk_params["folder_list"],max_lines-2,sdk_params["folder_scroll"],sdk_params["folder_pointer"],font,line_height,mouse_state)
            
            if act != None:
                if act[0] == "select": 
                    sdk_params["folder_pointer"] = act[1]
                elif act[0] == "scroll_down" and len(sdk_params["folder_list"])-sdk_params["folder_scroll"]-max_lines+2 > 0: sdk_params["folder_scroll"]+=1
                elif act[0] == "scroll_up" and sdk_params["folder_scroll"] > 0: sdk_params["folder_scroll"]-=1

            act = leitmotif.draw_button(screen,(opener_rect[0]+8,height_margin+line_height*(max_lines-1)+1,btn_width,line_height-2),"center",fetch_line("base","editor_load_pack"),font,mouse_state)
            if act != None and sdk_params["folder_pointer"] != None:
                with open(os.path.join(current_dir,"paks",sdk_params["folder_pointer"],"pack.json"),encoding="utf-8") as file:
                    pack_parameters = json.loads(file.read())
                    sdk_params["mode"] = "main"
                    sdk_params["consist_pointer"] = -1
                    sdk_loaded_pack["info"] = pack_parameters
                    sdk_loaded_pack["pos"]=[0,0]
                    sdk_loaded_pack["selection"]=(-1,-1,0,0)
                    sdk_params["folder_scroll"] = 0

            act = leitmotif.draw_button(screen,(opener_rect[0]+8+btn_width*2,height_margin+line_height*(max_lines-1)+1,btn_width,line_height-2),"center",fetch_line("base","editor_close_menu"),font,mouse_state)
            if act != None:
                sdk_params["mode"] = "main"
                sdk_params["folder_scroll"] = 0

        # пре-рендерилка
        if sdk_params["mode"] == "render": 
            opener_rect = (screen_size[0]/4-2,screen_size[1]/3-2,screen_size[0]/2+4,screen_size[1]/3+4)
            max_lines = int(opener_rect[3]//line_height)
            height_margin = opener_rect[1]+(opener_rect[3]-line_height*max_lines)/2
            btn_width = (opener_rect[2]-8)/4

            leitmotif.draw_window(screen,opener_rect)

            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

            leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin,opener_rect[2]-16,line_height),"center",fetch_line("base","editor_render_long"),font)
            if pack_render_thread.is_alive():
                leitmotif.draw_multitext(screen,(opener_rect[0]+8,height_margin+line_height,opener_rect[2]-16,0),render_log,max_lines-2,line_height,font)
                leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin+line_height*(max_lines-1),opener_rect[2]-16,line_height),"center",fetch_line("base","editor_render_progress").replace("%z",str(round(render_progress,2))),font)
            else:
                leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin+line_height*(max_lines/2-2),opener_rect[2]-16,line_height),"center",fetch_line("base","editor_render_desc1"),font)
                leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin+line_height*(max_lines/2-1),opener_rect[2]-16,line_height),"center",fetch_line("base","editor_render_desc2"),font)
                leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin+line_height*(max_lines/2),opener_rect[2]-16,line_height),"center",fetch_line("base","editor_render_proceed"),font)

                act = leitmotif.draw_button(screen,(opener_rect[0]+8+btn_width*2.5,height_margin+line_height*(max_lines/2+1),btn_width,line_height-2),"center",fetch_line("base","editor_render_yes"),font,mouse_state)
                if act != None:
                    pack_name = sdk_params["folder_pointer"]
                    render_progress = 0
                    pack_render_thread = threading.Thread(target=render)
                    pack_render_thread.start()

                act = leitmotif.draw_button(screen,(opener_rect[0]+8+btn_width*0.5,height_margin+line_height*(max_lines/2+1),btn_width,line_height-2),"center",fetch_line("base","editor_render_no"),font,mouse_state)
                if act != None:
                    sdk_params["mode"] = "main"

        # пре-рендерилка
        if sdk_params["mode"] == "render_complete": 
            opener_rect = (screen_size[0]/4-2,screen_size[1]/3-2,screen_size[0]/2+4,screen_size[1]/3+4)
            max_lines = int(opener_rect[3]//line_height)
            height_margin = opener_rect[1]+(opener_rect[3]-line_height*max_lines)/2
            btn_width = (opener_rect[2]-8)/4

            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]
            leitmotif.draw_window(screen,opener_rect)
            leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin,opener_rect[2]-16,line_height),"center",fetch_line("base","editor_render_long"),font)
            leitmotif.draw_label(screen,(opener_rect[0]+8,height_margin+line_height*(max_lines/2-1),opener_rect[2]-16,line_height),"center",fetch_line("base","editor_render_complete"),font)
            act = leitmotif.draw_button(screen,(opener_rect[0]+8+btn_width*1.5,height_margin+line_height*(max_lines/2),btn_width,line_height-2),"center",fetch_line("base","editor_render_no"),font,mouse_state)
            if act != None:
                sdk_params["mode"] = "main"

        #боковая панель для выбора состава
        if sdk_params["mode"] == "tiles" or sdk_mode_timers["tiles"] > 0:
            menu_height = main_font_height+menu_bar_vert_offset_bottom+menu_bar_vert_offset_top
            consist_rect = (screen_size[0]/4*(3+(1-sdk_mode_timers["tiles"])**2),
                menu_height,screen_size[0]/4-10,screen_size[1]/2-menu_height-10)
            max_lines = int(consist_rect[3]/line_height)
            consist_items = [q["name"] for q in sdk_loaded_pack["info"]["tiles"]] if sdk_loaded_pack["info"] != {} else []
            height_margin = (consist_rect[3]-max_lines*line_height)/2

            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

            leitmotif.draw_window(screen,consist_rect)

            leitmotif.draw_label(screen,(consist_rect[0]+8,consist_rect[1]+height_margin,consist_rect[2]-16,line_height),"center",fetch_line("base","editor_tile_mode"),font)

            act = leitmotif.draw_itemlist(screen, (consist_rect[0]+8,consist_rect[1]+height_margin+line_height,consist_rect[2]-16,0),consist_items,max_lines-1,sdk_params["tiles_scroll"],sdk_params["tiles_pointer"],font,line_height,mouse_state)

            if act != None:
                if act[0] == "select": 
                    sdk_params["tiles_pointer"] = act[1]
                    sdk_params["tiles_id"] = consist_items.index(act[1])
                elif act[0] == "scroll_down" and len(consist_items)-sdk_params["tiles_scroll"]-max_lines+2 > 0: sdk_params["tiles_scroll"]+=1
                elif act[0] == "scroll_up" and sdk_params["tiles_scroll"] > 0: sdk_params["tiles_scroll"]-=1

        #боковая панель для выбора состава
        if sdk_params["mode"] == "consist" or sdk_mode_timers["consist"] > 0:
            menu_height = main_font_height+menu_bar_vert_offset_bottom+menu_bar_vert_offset_top
            consist_rect = (screen_size[0]/4*(3+(1-sdk_mode_timers["consist"])**2),
                menu_height,screen_size[0]/4-10,screen_size[1]/2-menu_height-10)
            max_lines = int(consist_rect[3]/line_height)
            consist_items = [q["system_name"] for q in sdk_loaded_pack["info"]["consists"]] if sdk_loaded_pack["info"] != {} else []
            height_margin = (consist_rect[3]-max_lines*line_height)/2

            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

            leitmotif.draw_window(screen,consist_rect)

            leitmotif.draw_label(screen,(consist_rect[0]+8,consist_rect[1]+height_margin,consist_rect[2]-16,line_height),"center",fetch_line("base","editor_consist_mode"),font)

            act = leitmotif.draw_itemlist(screen, (consist_rect[0]+8,consist_rect[1]+height_margin+line_height,consist_rect[2]-16,0),consist_items,max_lines-1,sdk_params["consist_scroll"],sdk_params["consist_pointer"],font,line_height,mouse_state)

            if act != None:
                if act[0] == "select": 
                    sdk_params["consist_pointer"] = act[1]
                    sdk_params["consist_id"] = consist_items.index(act[1])
                    sdk_params["element_pointer"] = -1
                    sdk_loaded_pack["graphics"]["panel"] = pg.image.load(
                    os.path.join(*([current_dir,"paks",sdk_params["folder_pointer"],sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_sprite"]]))).convert_alpha()
                elif act[0] == "scroll_down" and len(consist_items)-sdk_params["consist_scroll"]-max_lines+2 > 0: sdk_params["consist_scroll"]+=1
                elif act[0] == "scroll_up" and sdk_params["consist_scroll"] > 0: sdk_params["consist_scroll"]-=1

        #боковая панель для выбора мира
        if sdk_params["mode"] == "world" or sdk_mode_timers["world"] > 0:
            menu_height = main_font_height+menu_bar_vert_offset_bottom+menu_bar_vert_offset_top
            world_rect = (screen_size[0]/4*(3+(1-sdk_mode_timers["world"])**2),
                menu_height,screen_size[0]/4-10,screen_size[1]/2-menu_height-10)
            max_lines = int(world_rect[3]/line_height)
            world_items = [q for q in sdk_loaded_pack["info"]["worlds"]] if sdk_loaded_pack["info"] != {} else []
            height_margin = (world_rect[3]-max_lines*line_height)/2
            button_width = (world_rect[2]-16-10)/2

            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

            leitmotif.draw_window(screen,world_rect)

            leitmotif.draw_label(screen,(world_rect[0]+8,world_rect[1]+height_margin,world_rect[2]-16,line_height),"center",fetch_line("base","editor_map_mode"),font)

            act = leitmotif.draw_itemlist(screen, (world_rect[0]+8,world_rect[1]+height_margin+line_height,world_rect[2]-16,0),world_items,max_lines-3,sdk_params["worlds_scroll"],sdk_params["worlds_pointer"],font,line_height,mouse_state)

            if act != None:
                if act[0] == "select": 
                    sdk_params["worlds_pointer"] = act[1]
                    sdk_params["worlds_name"] = act[1]
                    world = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["world"]
                    switches = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["switches"]
                    signals = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["signals"]

                    #sdk_params["consist_id"] = world_items.index(act[1])
                elif act[0] == "scroll_down" and len(world_items)-sdk_params["worlds_scroll"]-max_lines+2 > 0: sdk_params["worlds_scroll"]+=1
                elif act[0] == "scroll_up" and sdk_params["worlds_scroll"] > 0: sdk_params["worlds_scroll"]-=1

            act = leitmotif.draw_button(screen,(world_rect[0]+8,world_rect[1]+height_margin+line_height*(max_lines-2),button_width,line_height),"center",fetch_line("base","add"),font,mouse_state)

            if act != None:
                w_id = 0
                while f"world_{w_id}" in sdk_loaded_pack["info"]["worlds"]:
                    w_id+=1

                sdk_loaded_pack["info"]["worlds"][f"world_{w_id}"] = {"world":{},"signals":{},"switches":{}}
                sdk_params["worlds_pointer"] = f"world_{w_id}"
                sdk_params["worlds_name"] = f"world_{w_id}"
                world = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["world"]
                switches = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["switches"]
                signals = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]["signals"]

            act = leitmotif.draw_button(screen,(world_rect[0]+18+button_width,world_rect[1]+height_margin+line_height*(max_lines-2),button_width,line_height),"center",fetch_line("base","remove"),font,mouse_state)

            if act != None and sdk_params["worlds_pointer"] != None:
                sdk_loaded_pack["info"]["worlds"].pop(sdk_params["worlds_pointer"])
                world = {}
                switches = {}
                signals = {}
                sdk_params["worlds_pointer"] = None
                sdk_params["worlds_name"] = ""
                sdk_params["editor_mode"] = None

            leitmotif.draw_label(screen,(world_rect[0]+8,world_rect[1]+height_margin+line_height*(max_lines-1),world_rect[2]/4,line_height),"left",fetch_line("base","editor_name"),font)

            act = leitmotif.draw_textbox(screen,(world_rect[0]+8+world_rect[2]/4+8,world_rect[1]+height_margin+line_height*(max_lines-1),world_rect[2]/4*3-8-16,line_height),sdk_params["worlds_name"],font,mouse_state,sdk_params["editing"]=="world_name")

            if act != None:
                sdk_params["editing"] = "world_name"

            if sdk_params["editing"] == "world_name":
                sdk_params["worlds_name"] += unicode["chars"]

                if unicode["backspace"]: sdk_params["worlds_name"] = sdk_params["worlds_name"][:-1]
                if unicode["escape"]:
                    sdk_params["editing"] = None
                if unicode["return"]:
                    sdk_params["editing"] = None
                    temp = sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]]
                    sdk_loaded_pack["info"]["worlds"].pop(sdk_params["worlds_pointer"])
                    sdk_params["worlds_pointer"] = sdk_params["worlds_name"]
                    sdk_loaded_pack["info"]["worlds"][sdk_params["worlds_pointer"]] = temp

            speed = 8 if pressed[pg.K_RSHIFT] or pressed[pg.K_LSHIFT] else 2
            if (pressed[pg.K_LALT] or pressed[pg.K_RALT]): speed = 32
            if pressed[pg.K_DOWN]: 
                player_pos[1]+=speed*clock.get_fps()/60
            if pressed[pg.K_UP]: 
                player_pos[1]-=speed*clock.get_fps()/60
            if pressed[pg.K_LEFT]: 
                player_pos[0]-=speed*clock.get_fps()/60
            if pressed[pg.K_RIGHT]: 
                player_pos[0]+=speed*clock.get_fps()/60

        #редактор клеточек/путей
        if sdk_params["editor_mode"] == "tracks" or sdk_editor_mode_timers["tracks"] > 0:
            base_top_offset = 10
            toolbar_width = screen_size[0]/4-10
            toolbar_top_pos = screen_size[1]/2
            toolbar_left_pos = screen_size[0]/4*(3+(1-sdk_editor_mode_timers["tracks"])**2)
            toolbar_height = screen_size[1]-base_top_offset*2-toolbar_top_pos
            line_height = main_font_height+8
            max_lines = int((toolbar_height-8)/line_height)
            height_margin = (toolbar_height-max_lines*line_height)/2+base_top_offset+toolbar_top_pos

            itm = [icons[q] for q in toolbar]

            leitmotif.draw_window(screen,(toolbar_left_pos,toolbar_top_pos+base_top_offset,toolbar_width,toolbar_height))

            leitmotif.draw_label(screen,(toolbar_left_pos+8,height_margin,(toolbar_width-16),line_height),"center",fetch_line("base","editor_map_tiles"),font)

            act = leitmotif.draw_itemsel(screen,
                (toolbar_left_pos+14,height_margin+line_height,(toolbar_width-28),(max_lines-3)*line_height),
                itm,sdk_params["tile_placer_scroll"],sdk_params["tile_placer_pointer"],line_height,line_height*2-2,mouse_state
                
            )

            if act != None:
                if act[0] == "select":
                    sdk_params["tile_placer_pointer"] = act[1]
                elif act[0] == "scroll_down" and len(itm)-sdk_params["tile_placer_scroll"]-act[1]*act[2] > 0: sdk_params["tile_placer_scroll"]+=(act[1])
                elif act[0] == "scroll_up" and sdk_params["tile_placer_scroll"] > 0: sdk_params["tile_placer_scroll"]-=(act[1])

            act = leitmotif.draw_textbox(screen,(toolbar_left_pos+8,height_margin+line_height*(max_lines-2), toolbar_width-16,line_height),sdk_params["tile_placer_custom"][0],font,mouse_state, sdk_params["editing"] == "tile_placer_custom_0")

            if act != None:
                sdk_params["editing"] = "tile_placer_custom_0"
            if sdk_params["editing"] == "tile_placer_custom_0":
                sdk_params["tile_placer_custom"][0] += unicode["chars"]
                if unicode["backspace"]: sdk_params["tile_placer_custom"][0] = sdk_params["tile_placer_custom"][0][:-1]
                if unicode["escape"] or unicode["return"]:sdk_params["editing"] = None
                
            act = leitmotif.draw_textbox(screen,(toolbar_left_pos+8,height_margin+line_height*(max_lines-1), toolbar_width-16,line_height),sdk_params["tile_placer_custom"][1],font,mouse_state, sdk_params["editing"] == "tile_placer_custom_1")

            if act != None:
                sdk_params["editing"] = "tile_placer_custom_1"
            if sdk_params["editing"] == "tile_placer_custom_1":
                sdk_params["tile_placer_custom"][1] += unicode["chars"]
                if unicode["backspace"]: sdk_params["tile_placer_custom"][1] = sdk_params["tile_placer_custom"][1][:-1]
                if unicode["escape"] or unicode["return"]:sdk_params["editing"] = None

            if m_pos[0] < toolbar_left_pos and sdk_params["editor_mode"] == "tracks" and not clicked_on_menu_entry and mouse_clicked:
                m_world_pos = (player_pos[0]+m_pos[0]-screen_size[0]/2,
                               player_pos[1]+m_pos[1]-screen_size[1]/2)
                m_block_pos = (int((m_world_pos[0]-(editor_block_size[0] if m_world_pos[0] < 0 else 0))/editor_block_size[0]),
                            int((m_world_pos[1]-(editor_block_size[1] if m_world_pos[1] < 0 else 0))/editor_block_size[1]))
                m_block_pos = f"{m_block_pos[0]}:{m_block_pos[1]}"
                if m_btn[0] and sdk_params["tile_placer_pointer"] != None and m_block_pos not in world:
                    if toolbar[sdk_params["tile_placer_pointer"]] != "custom_tile":
                        world[m_block_pos] = [toolbar[sdk_params["tile_placer_pointer"]]]
                        if toolbar[sdk_params["tile_placer_pointer"]][-4:-1] in ["tsa","tsb","tsx"]:
                            switches[m_block_pos] = False
                    else:
                        world[m_block_pos] = [sdk_params["tile_placer_custom"][0],sdk_params["tile_placer_custom"][1]]
                        if sdk_params["tile_placer_custom"][0][-4:-1] in ["tsa","tsb","tsx"]:
                            switches[m_block_pos] = False
                elif m_btn[2] and m_block_pos in world:
                    world.pop(m_block_pos)
                    if m_block_pos in switches:
                        switches.pop(m_block_pos)
        
        #редактор сигналов
        if sdk_params["editor_mode"] == "signals" or sdk_editor_mode_timers["signals"] > 0:
            base_top_offset = 10
            toolbar_width = screen_size[0]/4-10
            toolbar_top_pos = screen_size[1]/2
            toolbar_left_pos = screen_size[0]/4*(3+(1-sdk_editor_mode_timers["signals"])**2)
            toolbar_height = screen_size[1]-base_top_offset*2-toolbar_top_pos
            line_height = main_font_height+8
            max_lines = int((toolbar_height-8)/line_height)
            height_margin = (toolbar_height-max_lines*line_height)/2+base_top_offset+toolbar_top_pos
            
            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

            if signal_editor_params["scroll"]+max_lines-5 > len(list(signals.keys())):
                signal_editor_params["scroll"] = max(0, signal_editor_params["scroll"]-(max_lines-5-len(list(signals.keys()))+signal_editor_params["scroll"]))

            leitmotif.draw_window(screen,(toolbar_left_pos,toolbar_top_pos+base_top_offset,toolbar_width,toolbar_height))

            leitmotif.draw_label(screen,(toolbar_left_pos+8,height_margin,(toolbar_width-16),line_height),"center",fetch_line("base","editor_map_signalling"),font)

            act = leitmotif.draw_itemlist(screen,
                (toolbar_left_pos+14,height_margin+line_height,toolbar_width-28,0),
                list(signals.keys()),max_lines-5,signal_editor_params["scroll"],signal_editor_params["current"],font,line_height,
                mouse_state)

            if act != None:
                if act[0] == "select": 
                    signal_editor_params["current"] = act[1]
                    signal_editor_params["editor_name"] = signal_editor_params["current"]
                    signal_editor_params["next"] = signals[signal_editor_params["current"]]["next"]
                    signal_editor_params["speed"] = signals[signal_editor_params["current"]]["speed"]
                elif act[0] == "scroll_down" and len(list(signals.keys()))-signal_editor_params["scroll"]-max_lines+6 > 0: signal_editor_params["scroll"]+=1
                elif act[0] == "scroll_up" and signal_editor_params["scroll"] > 0: signal_editor_params["scroll"]-=1

            
            button_width = (toolbar_width-16-10)/2 #(toolbar_width-16-20)/3

            act = leitmotif.draw_button(screen,(toolbar_left_pos+8,height_margin+line_height*(max_lines-4),button_width,line_height),
                "center",fetch_line("base","add"),font,mouse_state)
            
            if act != None: 
                if signal_editor_params["current"] != None and signal_editor_params["next"] != "" and signal_editor_params["next"] not in signals:
                    signals[signal_editor_params["next"]] = {"tiles":[],"next":"","speed":""}
                    signal_editor_params["current"] = signal_editor_params["next"]
                else:
                    base_id = 0
                    while f"SIG{base_id}" in signals:
                        base_id+=1
                    signals[f"SIG{base_id}"] = {"tiles":[],"next":"","speed":""}
                    signal_editor_params["current"] = f"SIG{base_id}"
                signal_editor_params["editor_name"] = signal_editor_params["current"]
                signal_editor_params["next"] = signals[signal_editor_params["current"]]["next"]
                signal_editor_params["speed"] = signals[signal_editor_params["current"]]["speed"]
                signal_editor_params["scroll"] = list(signals.keys()).index(signal_editor_params["current"])
                
            
            act = leitmotif.draw_button(screen,(toolbar_left_pos+8+10+button_width,height_margin+line_height*(max_lines-4),button_width,line_height),"center",fetch_line("base","remove"),font,mouse_state)
            
            if act != None: 
                if signal_editor_params["current"] != None:
                    signals.pop(signal_editor_params["current"])
                    signal_editor_params["current"] = None

            if signal_editor_params["current"] != None:
                leitmotif.draw_label(screen,(toolbar_left_pos+8,height_margin+line_height*(max_lines-3), toolbar_width/4,line_height),"left",fetch_line("base","editor_name"),font)
                act = leitmotif.draw_textbox(screen,(toolbar_left_pos+8+toolbar_width/4,height_margin+line_height*(max_lines-3), 3*toolbar_width/4-24,line_height),signal_editor_params["editor_name"],font,mouse_state, signal_editor_params["active"] == "editor_name")
                if act != None:
                    signal_editor_params["active"] = "editor_name"

                leitmotif.draw_label(screen,(toolbar_left_pos+8,height_margin+line_height*(max_lines-2), toolbar_width/4,line_height),"left",fetch_line("base","editor_next_signal"),font)
                act = leitmotif.draw_textbox(screen,(toolbar_left_pos+8+toolbar_width/4,height_margin+line_height*(max_lines-2), 3*toolbar_width/4-24,line_height),signal_editor_params["next"],font,mouse_state, signal_editor_params["active"] == "next")
                if act != None:
                    signal_editor_params["active"] = "next"

                leitmotif.draw_label(screen,(toolbar_left_pos+8,height_margin+line_height*(max_lines-1), toolbar_width/4,line_height),"left",fetch_line("base","editor_speed"),font)
                act = leitmotif.draw_textbox(screen,(toolbar_left_pos+8+toolbar_width/4,height_margin+line_height*(max_lines-1), 3*toolbar_width/4-24,line_height),signal_editor_params["speed"],font,mouse_state, signal_editor_params["active"] == "speed")
                if act != None:
                    signal_editor_params["active"] = "speed"

                if unicode["chars"] != "" or unicode["backspace"] or unicode["return"] or unicode["escape"]:
                    part_name_new = signal_editor_params[signal_editor_params["active"]]
                    if unicode["backspace"]:
                        part_name_new=part_name_new[:-1]
                    elif unicode["return"] or unicode["escape"]:
                        signal_editor_params["active"] = None
                    
                    part_name_new += unicode["chars"]

                    if unicode["return"] and signal_editor_params["active"] == "editor_name":
                        tmp = signals[signal_editor_params["current"]]
                        signals.pop(signal_editor_params["current"])
                        signal_editor_params["current"] = part_name_new
                        signals[signal_editor_params["current"]] = tmp
                        signal_editor_params["scroll"] = list(signals.keys()).index(signal_editor_params["current"])

                    if signal_editor_params["active"] == "speed": 
                        signals[signal_editor_params["current"]]["speed"] = part_name_new
                        signal_editor_params["speed"] = part_name_new
                    elif signal_editor_params["active"] == "next": 
                        signals[signal_editor_params["current"]]["next"] = part_name_new
                        signal_editor_params["next"] = part_name_new
                    elif signal_editor_params["active"] == "editor_name":
                        signal_editor_params["editor_name"] = part_name_new

            if (m_btn[0] + m_btn[1] + m_btn[2]) and signal_editor_params["current"] != None: 
                if m_pos[0] < toolbar_left_pos:
                    m_world_pos = (player_pos[0]+m_pos[0]-screen_size[0]/2,
                                player_pos[1]+m_pos[1]-screen_size[1]/2)
                    m_block_pos = (int(m_world_pos[0]//editor_block_size[0]),int(m_world_pos[1]//editor_block_size[1]))
                    if m_btn[0] and m_block_pos not in signals[signal_editor_params["current"]]["tiles"]:
                            signals[signal_editor_params["current"]]["tiles"].append(m_block_pos)
                    elif m_btn[2] and m_block_pos in signals[signal_editor_params["current"]]["tiles"]:
                        signals[signal_editor_params["current"]]["tiles"].remove(m_block_pos)

        # дефайнер/указатель графики для приборной панели
        if sdk_params["editor_mode"] == "graph_define" or sdk_editor_mode_timers["graph_define"] > 0:
            menu_height = main_font_height+menu_bar_vert_offset_bottom+menu_bar_vert_offset_top
            element_rect = (screen_size[0]/4*(3+(1-sdk_editor_mode_timers["graph_define"])**2),screen_size[1]/2+10,screen_size[0]/4-10,screen_size[1]/2-menu_height-10)
            max_lines = int(consist_rect[3]/line_height)
            height_margin = (consist_rect[3]-max_lines*line_height)/2
            button_width = (element_rect[2]-16-10)/2

            mouse_state = [m_pos[0], m_pos[1], mouse_clicked,(m_btn[0] or m_btn[2])]

            leitmotif.draw_window(screen,element_rect)

            items = list(sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"].keys()) if sdk_params["editor_mode"] == "graph_define" else []

            leitmotif.draw_label(screen,(element_rect[0]+8,element_rect[1]+height_margin,element_rect[2]-16,line_height),"center",fetch_line("base","editor_consist_locator"),font)

            act = leitmotif.draw_itemlist(screen,(element_rect[0]+8,element_rect[1]+height_margin+line_height,element_rect[2]-16,0),items,max_lines-3,sdk_params["element_scroll"],sdk_params["element_pointer"],font,line_height,mouse_state)
            
            if act != None:
                if act[0] == "select": 
                    sdk_params["element_pointer"] = act[1]
                    sdk_params["element_name"] = act[1]
                elif act[0] == "scroll_down" and len(items)-sdk_params["element_scroll"]-max_lines+3 > 0: sdk_params["element_scroll"]+=1
                elif act[0] == "scroll_up" and sdk_params["element_scroll"] > 0: sdk_params["element_scroll"]-=1

            add_button = leitmotif.draw_button(screen,(element_rect[0]+8,element_rect[1]+height_margin+line_height*(max_lines-2)+1,button_width,line_height-2),"center",fetch_line("base","add"),font,mouse_state)
            rm_button = leitmotif.draw_button(screen,(element_rect[0]+18+button_width,element_rect[1]+height_margin+line_height*(max_lines-2)+1,button_width,line_height-2),"center",fetch_line("base","remove"),font,mouse_state)
            leitmotif.draw_label(screen,(element_rect[0]+8,element_rect[1]+height_margin+line_height*(max_lines-1),(element_rect[2]-16)/3,line_height),"left",fetch_line("base","editor_name"),font)
            rename_btn = leitmotif.draw_textbox(screen,(element_rect[0]+8+(element_rect[2]-16)/3,element_rect[1]+height_margin+line_height*(max_lines-1),(element_rect[2]-16)/3*2,line_height),sdk_params["element_name"],font,mouse_state,sdk_params["editing"])

            if sdk_params["editing"]:
                element_name = sdk_params["element_name"]
                if unicode["return"]:
                        tmp = sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][sdk_params["element_pointer"]]
                        sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"].pop(sdk_params["element_pointer"])
                        sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][element_name] = tmp
                        sdk_params["element_pointer"] = element_name
                elif unicode["escape"]: sdk_params["editing"] = False
                elif unicode["backspace"]: element_name = element_name[:-1]
                else: element_name += unicode["chars"]
                
                sdk_params["element_name"] = element_name

            if add_button != None and mouse_clicked:
                sprite_id = 0
                while f"sprite_{sprite_id}" in sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"]:
                    sprite_id+=1
                sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"][f"sprite_{sprite_id}"] = {"x":0,"y":0,"w":1, "h":1,"scale":1}
                sdk_params["element_pointer"] = f"sprite_{sprite_id}"
                sdk_params["element_name"] = f"sprite_{sprite_id}"
                sdk_params["element_scroll"] = max(0,list(sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"].keys()).index(sdk_params["element_pointer"])-max_lines+4)
            elif rm_button and sdk_params["element_pointer"] != -1 and mouse_clicked:
                sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"].pop(sdk_params["element_pointer"])
                sdk_params["element_pointer"] = -1
                sdk_params["element_scroll"] = min(sdk_params["element_scroll"],len(sdk_loaded_pack["info"]["consists"][sdk_params["consist_id"]]["control_panel_info"])-max_lines+3)
            elif rename_btn and sdk_params["element_pointer"] != -1 and mouse_clicked:
                sdk_params["editing"] = True

    elif screen_state == "playing":
        opacity = (100-transition_timer if transition_act in ["appear",""] else transition_timer)
        if opacity != 100:
            blit_surface = pg.Surface(screen_size)
        else:
            blit_surface = screen
        screen.fill(tunnel_nothingness)
        blit_surface.fill(tunnel_nothingness)

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
        block_pos = [player_pos[0]//block_size[0],player_pos[1]//block_size[1]]
    

        # двухочерёдная система отрисовки
        # в первую очередь ложатся гарантированные тайлы уровня земли
        # во вторую очередь ложатся вагоны + тайлы, которые могут их перекрыть (пилоны, скамьи, иная шняга.)

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
                blit_surface.blit(
                    ground_sprites[object[2]][world_angle]
                    ,(round(screen_size[0]/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle))-w/2,0),
                    round(screen_size[1]/2+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-ground_sprites[object[2]]["height"]/compression-h/2,0)
                    )
                )
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
                if object[4] in reverse_signals and debug > 0:
                    color = (255,255,255)
                    if signal_states[reverse_signals[object[4]]["cur"]]["aspect"] == "red": color = (255,0,0)
                    elif signal_states[reverse_signals[object[4]]["cur"]]["aspect"] == "red_protector": color = (255,0,0)
                    elif signal_states[reverse_signals[object[4]]["cur"]]["aspect"] == "red_yellow": color = (255,128,0)
                    elif signal_states[reverse_signals[object[4]]["cur"]]["aspect"] == "yellow": color = (255,255,0)
                    elif signal_states[reverse_signals[object[4]]["cur"]]["aspect"] == "yellow_green": color = (128,255,0)
                    elif signal_states[reverse_signals[object[4]]["cur"]]["aspect"] == "green": color = (0,255,0)

                    pg.draw.polygon(blit_surface,color,(
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
                    ))


                if mouse_block_pos[0] == object[4][0] and mouse_block_pos[1] == object[4][1] and object[2][-4:-1] in ["tsa","tsb","tsx"]:
                    pg.draw.polygon(blit_surface,((0,0,255) if switches[mouse_block_pos] else (0,255,0)),(
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
                blit_surface.blit(
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
                    blit_surface.blit(
                        r_train_sprite,
                        (
                            round(screen_size[0]/2-r_train_sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),0),
                            round(screen_size[1]/2-r_train_sprite.get_height()/2-r_height/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6,0)
                        )
                    )
                    x_offset = -player_pos[0]+object[1][0]-object[4][0]
                    y_offset = -player_pos[1]+object[1][1]-object[4][1]
                    blit_surface.blit(
                        l_train_sprite,
                        (
                            round(screen_size[0]/2-l_train_sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),0),
                            round(screen_size[1]/2-l_train_sprite.get_height()/2-l_height/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6,0)
                        )
                    )
                else:
                    x_offset = -player_pos[0]+object[1][0]-object[4][0]
                    y_offset = -player_pos[1]+object[1][1]-object[4][1]
                    blit_surface.blit(
                        l_train_sprite,
                        (
                            round(screen_size[0]/2-l_train_sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),0),
                            round(screen_size[1]/2-l_train_sprite.get_height()/2-l_height/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6,0)
                        )
                    )
                    x_offset = -player_pos[0]+object[1][0]-object[4][0]
                    y_offset = -player_pos[1]+object[1][1]-object[4][1]
                    blit_surface.blit(
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
                    pg.draw.polygon(blit_surface,(255,0,0,),(
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
                    blit_surface.blit(text,(
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

        # звук

        sound_radius = 1600
        removal_list = []
        id_removal_list = []

        for train in valid:
            t_pos = trains[train[0]].pos
            dist = ((player_pos[0]-t_pos[0])**2+(player_pos[1]-t_pos[1])**2)**0.5
            linked_consist = trains[train[0]].consist
            if dist < sound_radius: 
                if linked_consist not in channel_dict:
                    ch_id = 0
                    while ch_id in roll_channels_occupied: ch_id +=1
                    roll_channels_occupied.append(ch_id)
                    channel_dict[linked_consist] = {"roll_channel":pg.mixer.Channel(ch_id*2),"ambient_channel":pg.mixer.Channel(ch_id*2+1),"new":None,"cur":None,"alive":False,"id":ch_id,"dist":dist}
                    if "ambient" in sounds[consists[linked_consist].train_type]: 
                        channel_dict[linked_consist]["ambient_channel"].play(sounds[consists[linked_consist].train_type]["ambient"],-1)
                channel_dict[linked_consist]["dist"] = min(channel_dict[linked_consist]["dist"],dist)
                found = False
                for mapping in consists[linked_consist].consist_info["drive_sounds"]:
                    if mapping[1] <= consists[linked_consist].velocity*3.6 and consists[linked_consist].velocity*3.6 <= mapping[2]:
                        channel_dict[linked_consist]["new"] = mapping[0]
                        found = True
                        break
                if not found: channel_dict[linked_consist]["new"] = None
                channel_dict[linked_consist]["alive"] = True

        for linked_consist in channel_dict:
            if not channel_dict[linked_consist]["alive"]:
                removal_list.append(linked_consist)
                id_removal_list.append(channel_dict[linked_consist]["id"])
            else:
                channel_dict[linked_consist]["roll_channel"].set_volume(round(volume*0.5*(1600-channel_dict[linked_consist]["dist"])/1600,3))
                channel_dict[linked_consist]["ambient_channel"].set_volume(round(volume*0.5*(1600-channel_dict[linked_consist]["dist"])/1600,3))
                channel_dict[linked_consist]["dist"] = sound_radius+1
                if channel_dict[linked_consist]["cur"] != channel_dict[linked_consist]["new"]:
                    channel_dict[linked_consist]["cur"] = channel_dict[linked_consist]["new"]
                    if channel_dict[linked_consist]["new"] == None:
                        channel_dict[linked_consist]["roll_channel"].stop()
                    else:
                        channel_dict[linked_consist]["roll_channel"].play(sounds[consists[linked_consist].train_type][channel_dict[linked_consist]["new"]],-1)

                channel_dict[linked_consist]["alive"] = False

        for rem in removal_list:
            channel_dict[rem]["roll_channel"].stop()
            channel_dict[rem]["ambient_channel"].stop()
            roll_channels_occupied.remove(channel_dict[rem]["id"])
            channel_dict.pop(rem)


        if controlling != -1 and controlling_consist != -1:
            
            panel = train_sprites["controls"][consists[controlling_consist].train_type]["panel"]

            hotkeys_check = [pressed[hotkeys[key]] or hotkeys[key] in keyups for key in hotkeys]

            if (screen_size[0]/2+panel.get_width()/2 >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2 and 
                screen_size[1] >= m_pos[1] >= screen_size[1]-panel.get_height() or True) or True in hotkeys_check:
                for elem_id, element in enumerate(consists[controlling_consist].consist_info["element_mapouts"]):
                    #if element["type"] != "analog_scale":
                    #print(element["draw_mappings"],element["name"],element["state"] if "state" in element else 0)
                    info = element["draw_mappings"][element["state"] if "state" in element else 0]
                    x,y,w,h = info[0], info[1],info[4], info[5]
                    scale = info[2]
                    if (screen_size[0]/2-panel.get_width()/2+x*scale+w*scale >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2+x*scale and 
                        screen_size[1]-panel.get_height()+y*scale+h*scale >= m_pos[1] >= screen_size[1]-panel.get_height()+y*scale) or hotkeys_check: 
                        if (screen_size[0]/2-panel.get_width()/2+x*scale+w*scale >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2+x*scale and 
                        screen_size[1]-panel.get_height()+y*scale+h*scale >= m_pos[1] >= screen_size[1]-panel.get_height()+y*scale):
                            annot_base = fetch_line(consists[controlling_consist].train_type,element["name"])
                            annotation = annot_base if element["type"] != "analog_scale" else str(annot_base).replace("%s",str(element["angle"]))
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
                blit_surface.blit(underlay,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))

            
            rr_direction = int(consists[controlling_consist].controlling_direction*(1-2*trains[controlling].reversed))
            rr = train_sprites["controls"][consists[controlling_consist].train_type][f"rr_{rr_direction}"]
            x,y = consists[controlling_consist].consist_info["rr_draw_mapouts"][str(rr_direction)]
            scale = consists[controlling_consist].consist_info["rr_draw_mapouts"]["scale"]
            blit_surface.blit(rr,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))

            blit_surface.blit(panel,(screen_size[0]/2-panel.get_width()/2,screen_size[1]-panel.get_height()))

            for element in consists[controlling_consist].consist_info["element_mapouts"]:
                if element["type"] != "analog_scale":
                    info = element["draw_mappings"][element["state"]]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = train_sprites["controls"][consists[controlling_consist].train_type][info[3]] 
                        x,y = info[0], info[1]
                        scale = info[2]
                        blit_surface.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
                    elif info[3] != None: print(f"Check sprite definitons! No {info[3]} found in {consists[controlling_consist].train_type}")
                else:
                    info = element["draw_mappings"][0]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = train_sprites["controls"][consists[controlling_consist].train_type][info[3]] 
                        x,y = info[0], info[1]
                        scale = info[2]
                        blit_surface.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
                    
                    info = element["draw_mappings"][1]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = pg.transform.rotate(train_sprites["controls"][consists[controlling_consist].train_type][info[3]],round(element["base_angle"]-element["multiplier"]*element["angle"],5))
                        local_x,local_y = info[0], info[1]
                        local_scale = info[2]
                        blit_surface.blit(sprite,(round(screen_size[0]/2-panel.get_width()/2+(x*scale+local_x*local_scale)-sprite.get_width()/2,2),float(screen_size[1]-panel.get_height()+(int(y*scale+local_y*local_scale)+0.5)-sprite.get_height()/2)))

                    info = element["draw_mappings"][2]
                    if info[3] in train_sprites["controls"][consists[controlling_consist].train_type]:
                        sprite = train_sprites["controls"][consists[controlling_consist].train_type][info[3]] 
                        x,y = info[0], info[1]
                        scale = info[2]
                        blit_surface.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))


            km = train_sprites["controls"][consists[controlling_consist].train_type]["km"]
            x,y = consists[controlling_consist].consist_info["km_draw_mapouts"][str(consists[controlling_consist].km)]
            scale = consists[controlling_consist].consist_info["km_draw_mapouts"]["scale"]
            blit_surface.blit(km,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
            
            tk = train_sprites["controls"][consists[controlling_consist].train_type]["tk"]
            x,y = consists[controlling_consist].consist_info["tk_draw_mapouts"][str(consists[controlling_consist].tk)]
            scale = consists[controlling_consist].consist_info["tk_draw_mapouts"]["scale"]
            blit_surface.blit(tk,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
            
            overlay = train_sprites["controls"][consists[controlling_consist].train_type]["overlay"]
            blit_surface.blit(overlay,(screen_size[0]/2-overlay.get_width()/2,screen_size[1]-overlay.get_height()))

            loco_light_base = pg.transform.scale(misc_sprites["loco_light_base"],(
                misc_sprites["loco_light_base"].get_width()*5,
                misc_sprites["loco_light_base"].get_height()*5
            ))
            blit_surface.blit(loco_light_base,(screen_size[0]-loco_light_base.get_width(),screen_size[1]/2-loco_light_base.get_height()/2))
            if consists[controlling_consist].controlling_direction != 0:
                lamp = trains[consists[controlling_consist].first_car if consists[controlling_consist].controlling_direction > 0 else consists[controlling_consist].last_car].signal_state
                lamp_types = []
                if lamp != None:
                    if lamp["aspect"] == "green":
                        lamp_types.append(((3,3),"loco_light_green"))
                    elif lamp["aspect"] == "yellow_green":
                        lamp_types.append(((3,3),"loco_light_green"))
                        lamp_types.append(((3,13),"loco_light_yellow"))
                    elif lamp["aspect"] == "yellow":
                        lamp_types.append(((3,13),"loco_light_yellow"))
                    elif lamp["aspect"] == "red_yellow":
                        lamp_types.append(((3,23),"loco_light_red_yellow"))
                    elif lamp["aspect"] in ["red","red_protector"]:
                        lamp_types.append(((3,33),"loco_light_red"))
                    else:
                        lamp_types.append(((3,43),"loco_light_white"))
                else:
                    lamp_types.append(((3,43),"loco_light_white"))
                
                for pos,lamp_type in lamp_types:
                    lamp_sprite = pg.transform.scale(misc_sprites[lamp_type],(
                        misc_sprites[lamp_type].get_width()*5,
                        misc_sprites[lamp_type].get_height()*5
                    ))
                    blit_surface.blit(lamp_sprite,(screen_size[0]-loco_light_base.get_width()+pos[0]*5,screen_size[1]/2-loco_light_base.get_height()/2+pos[1]*5))


            if annotation:
                width_max = 0
                lines = []
                for annotation_line in annotation.split("\n"):
                    lines.append(annotation_font.render(annotation_line, True, (255,255,255)))
                    if lines[-1].get_width() > width_max: width_max = lines[-1].get_width() 
                
                s = pg.Surface((width_max+8,(lines[-1].get_height()+2)*len(lines)+6))
                s.set_alpha(128)
                s.fill((0,0,0))
                blit_surface.blit(s, (m_pos[0]+10,m_pos[1]+20))
                for i,e in enumerate(lines):
                    blit_surface.blit(e, (m_pos[0]+10+(8+width_max)/2-e.get_width()/2,
                                    m_pos[1]+24+(lines[-1].get_height()+2)*i))


        if spawn_menu[1] > 0:
            div = 4 
            base_img_height = 200
            pg.draw.rect(blit_surface,(200,200,200),(screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2),0,screen_size[0]/div+128,screen_size[1]))
            spawn_menu_name = font.render(fetch_line("base","consist_spawn"),True,text_black)
            blit_surface.blit(spawn_menu_name, (screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)+screen_size[0]/div/2-spawn_menu_name.get_width()/2,100))

            sprite = train_sprites["sprites"][spawn_menu[3]]["closed"][world_angle]["r"]
            blit_surface.blit(sprite,(screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)+screen_size[0]/div/2-sprite.get_width()/2,base_img_height))
            sprite = train_sprites["sprites"][spawn_menu[3]]["closed"][world_angle]["l"]
            blit_surface.blit(sprite,(screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)+screen_size[0]/div/2-sprite.get_width()/2,base_img_height))

            #descriptions_texts = train_types[spawn_menu[2]]["name"].split("\n")
            text_height = 20
            text_delta = text_height + 4
            emu_type_height = base_img_height+20+sprite.get_height()
            repaint_height = emu_type_height+text_delta*len(fetch_line(spawn_menu[2],"emu_name").split("\n"))+30+15
            base_left_pos = screen_size[0]/div*((div-1)+(1-spawn_menu[1])**2)
            spawn_menu_blocks = [
                [emu_type_height,fetch_line("base","emu_type"),fetch_line(spawn_menu[2],"emu_name").split("\n")],
                [repaint_height,fetch_line("base","emu_repaint"),train_sprites["sprites"][spawn_menu[3]]["name"].split("\n")]
            ]
            for z in spawn_menu_blocks:
                block_height, block_name, block_set = z
                pg.draw.rect(blit_surface,(128,128,128),
                    (base_left_pos+5,
                    block_height-5,
                    screen_size[0]/div-10,
                    text_delta*len(block_set)+40
                ))
                for e, i in enumerate(block_set):
                    spawn_menu_text = font.render(i,True,text_black)
                    blit_surface.blit(spawn_menu_text, 
                        (base_left_pos+screen_size[0]/div/2-spawn_menu_text.get_width()/2,
                        block_height+text_delta*e
                    ))

                is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (block_height+text_delta*len(block_set) <= m_pos[1] <= block_height+(text_height+2)*len(block_set)+30) and m_btn[0]
            
                pg.draw.rect(blit_surface,(15,15,15),
                                (base_left_pos+12,
                                block_height+text_delta*len(block_set)+2,28,28))
                pg.draw.rect(blit_surface,(50,50,50),
                                (base_left_pos+10+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,28,28))
                pg.draw.rect(blit_surface,(100,100,100),
                                (base_left_pos+12+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,24,24))
                pg.draw.polygon(blit_surface,text_black,
                                (
                                    (base_left_pos+16+2*is_on_button,
                                    block_height+text_delta*len(block_set)+14+2*is_on_button),
                                    (base_left_pos+10+22+2*is_on_button,
                                    block_height+text_delta*len(block_set)+6+2*is_on_button),
                                    (base_left_pos+10+22+2*is_on_button,
                                    block_height+text_delta*len(block_set)+22+2*is_on_button),
                                ))
                
                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (block_height+(text_height+2)*len(block_set) <= m_pos[1] <= block_height+text_delta*len(block_set)+30) and m_btn[0]
                pg.draw.rect(blit_surface,(15,15,15),
                                (base_left_pos+screen_size[0]/div-30-10+2,
                                block_height+text_delta*len(block_set)+2,28,28))
                pg.draw.rect(blit_surface,(50,50,50),
                                (base_left_pos+screen_size[0]/div-30-10+2*is_on_button,
                                block_height+text_delta*len(block_set)+2*is_on_button,28,28))
                pg.draw.rect(blit_surface,(100,100,100),
                                (base_left_pos+screen_size[0]/div-30-10+2+2*is_on_button,
                                block_height+text_delta*len(block_set)+2+2*is_on_button,24,24))
                pg.draw.polygon(blit_surface,text_black,
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
                    spawn_menu[3] = consists_info[spawn_menu[2]]["default_skin"]

                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (emu_type_height+text_delta*len(spawn_menu_blocks[0][2]) <= m_pos[1] <= emu_type_height+text_delta*len(spawn_menu_blocks[0][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    spawn_menu[2] = list(consists_info.keys())[(list(consists_info.keys()).index(spawn_menu[2])+1)%len(consists_info.keys())]
                    spawn_menu[3] = consists_info[spawn_menu[2]]["default_skin"]

                is_on_button = (base_left_pos+10 <= m_pos[0] <= base_left_pos+40) and (repaint_height+text_delta*len(spawn_menu_blocks[1][2]) <= m_pos[1] <= repaint_height+text_delta*len(spawn_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    spawn_menu[3] = train_repaint_dictionary[spawn_menu[2]][train_repaint_dictionary[spawn_menu[2]].index(spawn_menu[3])-1]

                is_on_button = (base_left_pos+screen_size[0]/div-30-10 <= m_pos[0] <= base_left_pos+screen_size[0]/div-10) and (repaint_height+text_delta*len(spawn_menu_blocks[1][2]) <= m_pos[1] <= repaint_height+text_delta*len(spawn_menu_blocks[1][2])+30) and m_btn[0]
                if is_on_button and mouse_clicked:
                    spawn_menu[3] = train_repaint_dictionary[spawn_menu[2]][(train_repaint_dictionary[spawn_menu[2]].index(spawn_menu[3])+1)%len(train_repaint_dictionary[spawn_menu[2]])]
                    
            elif controlling == -1 and spawn_menu[0]:
                if mouse_clicked and m_btn[0]:
                    consist_key = random.randint(0,999)
                    while consist_key in consists: consist_key = random.randint(0,999)
                    consists[consist_key] = Consist(spawn_menu[2],spawn_menu[3],train_types[spawn_menu[2]],consists_info[spawn_menu[2]],consist_key,world,reverse_signals,[256*mouse_block_pos[0]+128,player_pos[1]+world_mouse_coord[1]])
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
            if (pressed[pg.K_LALT] or pressed[pg.K_RALT]): speed = 32
            if pressed[pg.K_DOWN]: 
                player_pos[1]+=speed*clock.get_fps()/60
            if pressed[pg.K_UP]: 
                player_pos[1]-=speed*clock.get_fps()/60
            if pressed[pg.K_LEFT]: 
                player_pos[0]-=speed*clock.get_fps()/60
            if pressed[pg.K_RIGHT]: 
                player_pos[0]+=speed*clock.get_fps()/60
            if pg.K_ESCAPE in keydowns and "disappear" not in transition_act:
                transition_act = "disappear:title"
                transition_timer = 100-transition_timer
                k = list(channel_dict.keys())
                for rem in k:
                    channel_dict[rem]["roll_channel"].stop()
                    channel_dict[rem]["ambient_channel"].stop()
                    roll_channels_occupied.remove(channel_dict[rem]["id"])
                    channel_dict.pop(rem)
                for link in list(consists.keys()):
                    consists[link].exists = False
                    consists.pop(link)
                for link in list(trains.keys()):
                    trains[link].exists = False
                    trains.pop(link)
                signal_system.is_working = False
            if pg.K_s in keydowns:
                spawn_menu[0] = not(spawn_menu[0])
                if spawn_menu[2] == None: 
                    spawn_menu[2] = list(consists_info.keys())[0]
                if spawn_menu[3] == None: 
                    spawn_menu[3] = consists_info[spawn_menu[2]]["default_skin"]
        else:
            player_pos = [trains[controlling].pos[0],trains[controlling].pos[1]]

            if pg.K_s in keydowns and spawn_menu[0]:
                spawn_menu[0] = not(spawn_menu[0])

            if pg.K_UP in keydowns and consists[controlling_consist].km < consists[controlling_consist].consist_info["max_km"]:
                consists[controlling_consist].km += 1
            elif pg.K_DOWN in keydowns and consists[controlling_consist].km > consists[controlling_consist].consist_info["min_km"]:
                consists[controlling_consist].km -= 1

            if pg.K_f in keydowns and consists[controlling_consist].tk < consists[controlling_consist].consist_info["max_tk"]:
                consists[controlling_consist].tk += 1
            elif pg.K_r in keydowns and consists[controlling_consist].tk > consists[controlling_consist].consist_info["min_tk"]:
                consists[controlling_consist].tk -= 1

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
            if ("ars_beep" in sounds[consists[controlling_consist].train_type] and 
                not consists[controlling_consist].control_wires["ars_fuse"] and
                consists[controlling_consist].control_wires["ars"]):
                if not ars_beep_channel.get_busy():
                    ars_beep_channel.play(sounds[consists[controlling_consist].train_type]["ars_beep"],-1)
            else:
                ars_beep_channel.stop()
            
            if pressed[pg.K_ESCAPE]:
                ars_beep_channel.stop()

                controlling = -1
                controlling_consist = -1

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
                blit_surface.blit(line, (0, 20*i))

        if opacity != 100:
            blit_surface.convert()
            blit_surface.set_alpha(255*(opacity/100))
            screen.blit(blit_surface,(0,0))

        if spawn_menu[0] and spawn_menu[1] < 1:
            spawn_menu[1] += clock.get_fps()/60*0.0167
            if spawn_menu[1] > 1: spawn_menu[1] = 1
        elif not spawn_menu[0] and spawn_menu[1] > 0:
            spawn_menu[1] -= clock.get_fps()/60*0.0167
            if spawn_menu[1] < 0: spawn_menu[1] = 0

    elif screen_state == "exit": #техническое состояние для выхода из игры
        working = False

    elif screen_state == "load_start": #техническое состояние для загрузки пакетов после включения/выключения
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
        
        with open("config.json") as f:
            config = json.loads(f.read())

        volume = config["volume"]
        selected_locale = config["selected_locale"]

        sprite_thread = threading.Thread(target=sprite_load_routine,daemon=True) #,args=[world]
        sprite_thread.start()

    elif screen_state == "sdk_load": #техническое состояние для прогрузки пакетов в SDK
        player_pos = [0,0]

        for key in sdk_mode_timers: sdk_mode_timers[key] = 0

        for key in sdk_editor_mode_timers: sdk_editor_mode_timers[key] = 0
        
        for param in base_sdk_params: sdk_params[param] =  base_sdk_params[param]

        sdk_params["folder_list"] = []
        pak_folders = os.listdir(os.path.join(current_dir,"paks"))

        for folder in pak_folders:
            folder_contents = os.listdir(os.path.join(current_dir,"paks",folder))
            if "pack.json" in folder_contents:
                sdk_params["folder_list"].append(folder)
        screen_state = "sdk"

    elif screen_state == "pack_chooser_open": #техническое состояние для открытия селектора пакетов
        pack_chooser_params = {"all":[],"disabled":[],"scroll":0,"selected":None}
        pak_folders = os.listdir(os.path.join(current_dir,"paks"))

        for folder in pak_folders:
            folder_contents = os.listdir(os.path.join(current_dir,"paks",folder))
            if "pack.json" in folder_contents:
                pack_chooser_params["all"].append(folder)

        with open("config.json") as f:
            pack_chooser_params["disabled"] = json.loads(f.read())["disabled_packs"]
        
        screen_state = "pack_chooser"

    elif screen_state == "world_chooser_open": # техническое состояние для открытия селектора пакетов
        pak_folders = os.listdir(os.path.join(current_dir,"paks"))
        world_chooser_params = {"paks":[],"worlds":[],"scroll":0,"selected":None}

        for folder in pak_folders:
            folder_contents = os.listdir(os.path.join(current_dir,"paks",folder))
            if "pack.json" in folder_contents:
                with open(f"paks\{folder}\pack.json",encoding="utf-8") as file:
                    q = json.loads(file.read())
                    if "worlds" in q and len(q["worlds"]):
                        world_chooser_params["paks"] += [folder]*len(q["worlds"])
                        for w in q["worlds"]:
                            world_chooser_params["worlds"] += [w]
        screen_state = "world_chooser"

    elif screen_state == "play_load": # техническое состояние для загрузки сигналки перед игрой

        with open(f"paks\{world_pack}\pack.json") as world_file:
            info = json.loads(world_file.read())["worlds"][world_name]

            world = {}
            for key in info["world"]:
                x,y = map(int,key.split(":"))
                world[(x,y)] = info["world"][key]

            switches = {}
            for key in info["switches"]:
                x,y = map(int,key.split(":"))
                switches[(x,y)] = info["switches"][key]

            signals = {}
            for key in info["signals"]:
                signals[key] = info["signals"][key]
                new_tiles = []
                for tile in signals[key]["tiles"]:
                    new_tiles.append(tuple(tile))
                signals[key]["tiles"] = new_tiles

        reverse_signals = {}
        for sig_id in signals:
            for tile in signals[sig_id]["tiles"]: 
                reverse_signals[tile] = {"cur":sig_id}
                if "next" in signals[sig_id]: reverse_signals[tile]["next"] = signals[sig_id]["next"]

        signal_system = SignalSystem(signals)
        screen_state = "playing"
    
    #таймер переходняка
    if transition_timer > 0:
        transition_timer -= 1/(30/max(clock.get_fps(),1))

        if transition_timer <= 0 and transition_act != "":
            transition_timer = 0
            if ":" in transition_act:
                screen_state = transition_act.split(":")[1]
                transition_act = "appear"
                transition_timer = 100
            else:
                transition_act = ""

    #блок обработки таймеров
    for timer in sdk_mode_timers:
        if timer != sdk_params["mode"] and sdk_mode_timers[timer] > 0:
            sdk_mode_timers[timer] = max(0, sdk_mode_timers[timer]-clock.get_fps()/30*0.0167)
        elif timer == sdk_params["mode"] and sdk_mode_timers[timer] < 1 and sum(sdk_mode_timers.values())-sdk_mode_timers[timer] == 0:
            sdk_mode_timers[timer] = min(1, sdk_mode_timers[timer]+clock.get_fps()/30*0.0167)

    for timer in sdk_editor_mode_timers:
        if timer != sdk_params["editor_mode"] and sdk_editor_mode_timers[timer] > 0:
            sdk_editor_mode_timers[timer] = max(0, sdk_editor_mode_timers[timer]-clock.get_fps()/30*0.0167)
        elif timer == sdk_params["editor_mode"] and sdk_editor_mode_timers[timer] < 1 and sum(sdk_editor_mode_timers.values())-sdk_editor_mode_timers[timer] == 0:
            sdk_editor_mode_timers[timer] = min(1, sdk_editor_mode_timers[timer]+clock.get_fps()/30*0.0167)

    pg.display.update()
    clock.tick(60)
    frame_cnt+=1
    total_frame_cnt+=1
    if not working:
        pg.quit()