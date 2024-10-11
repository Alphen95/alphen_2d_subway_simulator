import pygame as pg
import os
import json
import pathlib

version = "v0.3 изометрия. ленивая, но рабочая."
scale = 1
CURRENT_DIRECTORY = pathlib.Path(__file__).parent.resolve()
current_dir = CURRENT_DIRECTORY

from train import *



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

pg.init()
clock = pg.time.Clock()
screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
font = pg.font.Font(os.path.join(CURRENT_DIRECTORY,"res","verdana.ttf"),20)
annotation_font = pg.font.Font(os.path.join(CURRENT_DIRECTORY,"res","verdana.ttf"),12)
screen_size = screen.get_size()
screen = pg.display.set_mode(screen_size)
pg.display.set_caption(f"Alphen's Subway Simulator v{version}")

sprite_loading_info = [
    {"name":"tstr","filename":"tracks","params":[0,0,64,256,1,0,False,False]},
    {"name":"tca1","filename":"tracks","params":[64,0,64,256,1,0,False,False]},
    {"name":"tca2","filename":"tracks","params":[128,0,64,256,1,0,False,False]},
    {"name":"tcb1","filename":"tracks","params":[64,0,64,256,1,0,True,False]},
    {"name":"tcb2","filename":"tracks","params":[128,0,64,256,1,0,True,False]},
    {"name":"tsa1","filename":"tracks","params":[192,0,64,256,1,0,False,False]},
    {"name":"tsa2","filename":"tracks","params":[256,0,64,256,1,0,False,False]},
    {"name":"tsb1","filename":"tracks","params":[192,0,64,256,1,0,True,False]},
    {"name":"tsb2","filename":"tracks","params":[256,0,64,256,1,0,True,False]},

    {"name":"stroitelnaya_walls","filename":"platform","params":[64*3,256+512,64,256,29,3,False,False]},
    {"name":"stroitelnaya_platform","filename":"platform","params":[0,256+512,64,256,3,0,False,False]},
    {"name":"stroitelnaya_track_tstr","filename":"platform","params":[0,512+512,64,256,3,0,False,False]},
    {"name":"stroitelnaya_walls_f","filename":"platform","params":[64*3,256+512,64,256,29,3,True,False]},
    {"name":"stroitelnaya_platform_f","filename":"platform","params":[0,256+512,64,256,3,0,True,False]},
    {"name":"stroitelnaya_track_f_tstr","filename":"platform","params":[0,512+512,64,256,3,0,True,False]},

    {"name":"sodovaya_walls","filename":"platform","params":[64*3,256*5,64,256,29,3,False,False]},
    {"name":"sodovaya_platform","filename":"platform","params":[0,256*5,64,256,3,0,False,False]},
    {"name":"sodovaya_track_tstr","filename":"platform","params":[0,256*6,64,256,32,0,False,False]},
    {"name":"sodovaya_walls_f","filename":"platform","params":[64*3,256*5,64,256,29,3,True,False]},
    {"name":"sodovaya_platform_f","filename":"platform","params":[0,256*5,64,256,3,0,True,False]},
    {"name":"sodovaya_track_f_tstr","filename":"platform","params":[0,256*6,64,256,3,0,True,False]},
]
ground_sprites = {}

temp_sprites = {}
filenames = os.listdir(os.path.join(CURRENT_DIRECTORY,"res"))
for filename in filenames:
    if filename[-4:] == ".png":
        temp_sprites[filename[:-4]] = pg.image.load(os.path.join(*([current_dir,"res",filename]))).convert_alpha()

for info_pack in sprite_loading_info:

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
    ground_sprites[info_pack["name"]]["height"] = (info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor-1
    

train_sprites = {}
train_types = {}
sounds = {}
consists_info = {}

pg.mixer.init()
channel_rolling = pg.mixer.Channel(1)
channel_rolling.set_volume(0.125)

train_folders = os.listdir(os.path.join(current_dir,"trains"))
for folder in train_folders:
    folder_contents = os.listdir(os.path.join(current_dir,"trains",folder))
    if "train.json" in folder_contents:
        
        with open(os.path.join(CURRENT_DIRECTORY,"trains",folder,"train.json"),encoding="utf-8") as file:
            train_parameters = json.loads(file.read())
            base_train_sprite = pg.image.load(os.path.join(*([current_dir,"trains",folder,"sprite.png"]))).convert_alpha()
            base_control_panel_sprite = pg.image.load(os.path.join(*([current_dir,"trains",folder,"controls.png"]))).convert_alpha()
            key = train_parameters["system_name"]
            train_sprites[key] = {}
            consists_info[key] = train_parameters["traction_info"]
            base_layers = []
            sprite_stack_factor = 4

            sprite_params = train_parameters["sprite_info"]["train"]

            for i in range(sprite_params["layers"]):
                x_pos = sprite_params["w"]*i# if not ("reversed" in sprite_params and sprite_params["reversed"]) else sprite_params["h_layer"]*(sprite_params["layer_amount"]-1-i)
                base_layers.append(pg.transform.scale(base_train_sprite.subsurface(x_pos,0,sprite_params["w"],sprite_params["h"]),(sprite_params["w"]*4,sprite_params["h"]*4)))


            for rotation in [*range(0,360,5)]+[8.25+world_angle,16.5+world_angle,-8.25+world_angle,-16.5+world_angle,180-8.25+world_angle,180-16.5+world_angle,180+8.25+world_angle,180+16.5+world_angle]:
                w, h = pg.transform.rotate(base_layers[0],rotation).get_size()
                h/=compression
                rotation = rotation%360

                surface = pg.Surface((w,h+sprite_params["layers"]*sprite_stack_factor-1))
                surface.set_colorkey((0,0,0))

                for i in range(sprite_params["layers"]*sprite_stack_factor):
                    pos = (0,surface.get_height()-i-h)
                    sprite = pg.transform.rotate(base_layers[int(i/sprite_stack_factor)],rotation)
                    surface.blit(pg.transform.scale(sprite,(sprite.get_width(),sprite.get_height()/compression)),pos)
                train_sprites[key][rotation] = surface
            train_sprites[key]["height"] = sprite_params["layers"]*sprite_stack_factor-1


            controls_info = train_parameters["control_panel_info"]
            train_sprites[key]["controls"] = {}
            for control in controls_info:
                train_sprites[key]["controls"][control] = pg.transform.scale(
                    base_control_panel_sprite.subsurface(controls_info[control]["x"],controls_info[control]["y"],controls_info[control]["w"],controls_info[control]["h"]),
                    (controls_info[control]["w"]*controls_info[control]["scale"],controls_info[control]["h"]*controls_info[control]["scale"]))

            train_types[key] = {}
            train_types[key]["size"] = (*train_parameters["clickable_size"],sprite_params["layers"]*sprite_stack_factor-1)

            sounds[key] = {}
            for sound in train_parameters["sound_loading_info"]:
                sounds[key][sound] = pg.mixer.Sound(os.path.join(CURRENT_DIRECTORY,"trains",folder,train_parameters["sound_loading_info"][sound]))
                sounds[key][sound].set_volume(0.5)

world = {
    (0,2):["tstr"],
    (0,1):["tsb1"],(-1,1):["tcb2"],
    (1,0):["stroitelnaya_platform_f","stroitelnaya_walls_f"],(0,0):["stroitelnaya_track_f_tstr"],(-1,0):["stroitelnaya_track_tstr"],(-2,0):["stroitelnaya_platform","stroitelnaya_walls"],
    (0,-1):["tstr"],(-1,-1):["tstr"],
    (1,-2):["tca2"],(0,-2):["tca1"],(-1,-2):["tcb1"],(-2,-2):["tcb2"],
    (1,-3):["tstr"],(-2,-3):["tstr"],
    (1,-4):["sodovaya_track_tstr"],(0,-4):["sodovaya_platform","sodovaya_walls"],(-1,-4):["sodovaya_platform_f","sodovaya_walls_f"],(-2,-4):["sodovaya_track_f_tstr"],
    (1,-5):["tcb1"],(0,-5):["tcb2"],(-1,-5):["tca2"],(-2,-5):["tca1"],
    (0,-6):["tsa2"],(-1,-6):["tca1"],
    (0,-7):["tstr"]}

'''
world = {
    (0,2):"tstr",
    (0,1):"tsb1",(-1,1):"tcb2",
    (1,0):"tozolosh_platform_r",(0,0):"tozolosh_track_r_tstr",(-1,0):"tozolosh_track_l_tstr",(-2,0):"tozolosh_platform_l",
    (0,-1):"tstr",(-1,-1):"tstr",
    (0,-2):"tstr",(-1,-2):"tstr",
    (1,-3):"tca2",(0,-3):"tca1",(-1,-3):"tcb1",(-2,-3):"tcb2",
    (1,-4):"tstr",(-2,-4):"tstr",
    (1,-5):"tstr",(-2,-5):"tstr",
    (1,-6):"aktau_track_l_tstr",(0,-6):"aktau_platform_l",(-1,-6):"aktau_platform_r",(-2,-6):"aktau_track_r_tstr",
    (1,-7):"tstr",(-2,-7):"tstr",
    (1,-8):"tcb1",(0,-8):"tcb2",(-1,-8):"tca2",(-2,-8):"tca1",
    (0,-9):"tstr",(-1,-9):"tstr",
    (0,-10):"tsa2",(-1,-10):"tsa1",
    (0,-11):"tstr",(-1,-11):"tstr",
}
'''
switches = {
    (0,1):False,
    (0,-10):True,
    (0,-6):True,
    (-1,-10):True
}

#trains = {}
consists = {}
consist_key = random.randint(0,999)
consists[consist_key] = Consist("type_a",train_types["type_a"],consists_info["type_a"],consist_key,world,[256*1.5,1024*-3.5])

player_pos = [256*0.5,1024*-2.5]
m_btn = [0,0,0]
mouse_clicked = False
mouse_released = False

while working:
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
                [(train.pos[0],train.pos[1]),train.type,train.angle,train.reversed,train.size])
    if controlling != -1: player_pos = [trains[controlling].pos[0],trains[controlling].pos[1]-screen_size[1]/8*2*(1 if 90 <= (trains[controlling].angle+trains[controlling].reversed*180)%360 <= 270 else -1)]
    block_pos = [int((player_pos[0]-(block_size[0] if player_pos[0] < 0 else 0))/block_size[0]),int((player_pos[1]-(block_size[1] if player_pos[1] < 0 else 0))/block_size[1])]

    keydowns = []
    mouse_clicked_prev = mouse_clicked
    mouse_clicked = False
    mouse_released = False
    for evt in pg.event.get():
        if evt.type == pg.QUIT:
            working = False
        if evt.type == pg.KEYDOWN:
            keydowns.append(evt.key)
            if evt.key == pg.K_d:
                debug = (debug+1)%3
        if evt.type == pg.MOUSEBUTTONDOWN and not m_btn[0] and not m_btn[2]:
            mouse_clicked = True
        elif evt.type == pg.MOUSEBUTTONUP:
            mouse_released = True


    screen.fill((25,25,25))
    object_draw_queue = []
    for tile_x in reversed(range(-int(screen_size[0]/block_size[0])-1,int(screen_size[0]/block_size[0])+2)):
        for tile_y in range(-int(screen_size[1]/block_size[1])-1,int(screen_size[1]/block_size[1])+2):
            #pg.draw.rect(screen,(255,0,0),)
            x_offset = (block_pos[0]+tile_x)*block_size[0]
            y_offset = (block_pos[1]+tile_y)*block_size[1]

            if (block_pos[0]+tile_x,block_pos[1]+tile_y) in world:
                tile_world_position = (block_pos[0]+tile_x,block_pos[1]+tile_y)

                if world[tile_world_position][0] in ground_sprites:
                    object_draw_queue.append([
                        "world",
                        (x_offset,y_offset),
                        world[tile_world_position][0],
                        (
                            tile_x*block_size[0],
                            tile_y*block_size[1]
                        )

                    ])
    for object in sorted(object_draw_queue,key= lambda z:(z[1][1],-z[1][0])):
        if object[0] == "world":
            w, h = ground_sprites[object[2]][world_angle].get_size()
            x_offset = object[3][0]+block_size[0]/2-player_pos[0]%(block_size[0])
            y_offset = object[3][1]+block_size[1]/2-player_pos[1]%(block_size[1])
            screen.blit(
                #pg.transform.scale(
                ground_sprites[object[2]][world_angle]#,block_size)
                ,(screen_size[0]/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle))-w/2,
                screen_size[1]/2+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-ground_sprites[object[2]]["height"]/compression-h/2
                )
            )

    object_draw_queue = []
    for tile_x in reversed(range(-int(screen_size[0]/block_size[0])-1,int(screen_size[0]/block_size[0])+2)):
        for tile_y in range(-int(screen_size[1]/block_size[1])-1,int(screen_size[1]/block_size[1])+2):
            #pg.draw.rect(screen,(255,0,0),)
            x_offset = (block_pos[0]+tile_x)*block_size[0]+block_size[0]
            y_offset = (block_pos[1]+tile_y)*block_size[1]

            if (block_pos[0]+tile_x,block_pos[1]+tile_y) in world:
                tile_world_position = (block_pos[0]+tile_x,block_pos[1]+tile_y)

                if len(world[tile_world_position]) > 1 and world[tile_world_position][1] in ground_sprites:
                    object_draw_queue.append([
                        "world",
                        (x_offset,y_offset),
                        world[tile_world_position][1],
                        (
                            tile_x*block_size[0],
                            tile_y*block_size[1]
                        )

                    ])

        

        if block_pos[0]+tile_x in valid_draw:
            for i, train_params in enumerate(sorted(valid_draw[block_pos[0]+tile_x],key=lambda x:x[1])):
                angle = (((train_params[2]+world_angle)%360 if (train_params[2]+world_angle)%360 in train_sprites[train_params[1]] else (train_params[2]+world_angle)//5*5))%360
                sprite = train_sprites[train.type][(angle+train_params[3]*180)%360]
                x_offset = train_params[0][0]-(train_params[4][0]*math.cos(math.radians(180-angle+world_angle))/2-train_params[4][1]*math.sin(math.radians(180-angle+world_angle))/2)
                y_offset = train_params[0][1]-(train_params[4][0]*math.sin(math.radians(180-angle+world_angle))/2+train_params[4][1]*math.cos(math.radians(180-angle+world_angle))/2)
                
                object_draw_queue.append([
                        "train",
                        (x_offset,y_offset),
                        train.type,
                        (angle+train_params[3]*180)%360,
                        (-(train_params[4][0]*math.cos(math.radians(180-angle+world_angle))/2-train_params[4][1]*math.sin(math.radians(180-angle+world_angle))/2),
                         -(train_params[4][0]*math.sin(math.radians(180-angle+world_angle))/2+train_params[4][1]*math.cos(math.radians(180-angle+world_angle))/2))
                    ])
                
    
    for object in sorted(object_draw_queue,key= lambda z:z[1][1]-z[1][0]): #олег помог с сортировкой #ОЛЕГКОГДАВИСТЕРИЯ
        if object[0] == "world":
            w, h = ground_sprites[object[2]][world_angle].get_size()
            x_offset = object[3][0]+block_size[0]/2-player_pos[0]%(block_size[0])
            y_offset = object[3][1]+block_size[1]/2-player_pos[1]%(block_size[1])
            screen.blit(
                #pg.transform.scale(
                ground_sprites[object[2]][world_angle]#,block_size)
                ,(screen_size[0]/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle))-w/2,
                screen_size[1]/2+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-ground_sprites[object[2]]["height"]/compression-h/2
                )
            )
        elif object[0] == "train":
            sprite = train_sprites[object[2]][object[3]]
            x_offset = -player_pos[0]+object[1][0]-object[4][0]
            y_offset = -player_pos[1]+object[1][1]-object[4][1]
            screen.blit(
                sprite,
                (
                    screen_size[0]/2-sprite.get_width()/2+x_offset*math.cos(math.radians(360-world_angle))-y_offset*math.sin(math.radians(360-world_angle)),
                    screen_size[1]/2-sprite.get_height()/2-train_sprites[train_params[1]]["height"]/compression+(x_offset*math.sin(math.radians(360-world_angle))+y_offset*math.cos(math.radians(360-world_angle)))/compression-6
                )
            )
    
    if debug:
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

    '''
    #if mouse_clicked and m_btn[0]:
    for train_params in sorted(valid,key=lambda x:x[1],reverse=True):
        localized_m_pos = (player_pos[0]+m_pos[0]-screen_size[0]/2,player_pos[1]+m_pos[1]-screen_size[1]/2)
        train = trains[train_params[0]]
        if train.pos[0]-train.size[0] < localized_m_pos[0] < train.pos[0]+train.size[0] and train.pos[1]-train.size[1] < localized_m_pos[1] < train.pos[1]+train.size[1]+train.size[2]:
            x_coords = []
            y_coords = []
            for i in range(2):
                x_coords.append(train.pos[0]+(train.size[0]*math.cos(math.radians(train.angle))/2+train.size[1]*math.sin(math.radians(train.angle))/2))
                x_coords.append(train.pos[0]-(train.size[0]*math.cos(math.radians(train.angle))/2-train.size[1]*math.sin(math.radians(train.angle))/2))
                x_coords.append(train.pos[0]-(train.size[0]*math.cos(math.radians(train.angle))/2+train.size[1]*math.sin(math.radians(train.angle))/2))
                x_coords.append(train.pos[0]+(train.size[0]*math.cos(math.radians(train.angle))/2-train.size[1]*math.sin(math.radians(train.angle))/2))
                y_coords.append(train.pos[1]+(train.size[1]*math.cos(math.radians(train.angle))/2-train.size[0]*math.sin(math.radians(train.angle))/2)-train.size[2]*i)
                y_coords.append(train.pos[1]+(train.size[1]*math.cos(math.radians(train.angle))/2+train.size[0]*math.sin(math.radians(train.angle))/2)-train.size[2]*i)
                y_coords.append(train.pos[1]-(train.size[1]*math.cos(math.radians(train.angle))/2-train.size[0]*math.sin(math.radians(train.angle))/2)-train.size[2]*i)
                y_coords.append(train.pos[1]-(train.size[1]*math.cos(math.radians(train.angle))/2+train.size[0]*math.sin(math.radians(train.angle))/2)-train.size[2]*i)
            colors = [(255,0,0),(0,255,0),(0,0,255),(255,255,0)]
            #pg.draw.polygon(screen,(255,0,0),[(x_coords[i]-player_pos[0]+screen_size[0]/2,y_coords[i]-player_pos[1]+screen_size[1]/2) for i in range(4)])
            for i in range(4):
                pg.draw.circle(screen,colors[i],(x_coords[i]-player_pos[0]+screen_size[0]/2,y_coords[i]-player_pos[1]+screen_size[1]/2),4)
            for i in range(4):
                pg.draw.circle(screen,colors[i],(x_coords[i+4]-player_pos[0]+screen_size[0]/2,y_coords[i+4]-player_pos[1]+screen_size[1]/2),4)
    ''' #нахуй не нужная хуйня

    '''
    for train_params in sorted(valid,key=lambda x:x[1]):
        if controlling == -1:
            localized_m_pos = (player_pos[0]+m_pos[0]-screen_size[0]/2,player_pos[1]+m_pos[1]-screen_size[1]/2)
            train = trains[train_params[0]]
            trains[train_params[0]].switches = switches
            width = abs(train.size[0]*math.cos(math.radians(train.angle))/2-train.size[1]*math.sin(math.radians(train.angle))/2) 
            height = abs(train.size[1]*math.cos(math.radians(train.angle))/2-train.size[0]*math.sin(math.radians(train.angle))/2)
            if train.pos[0]-width< localized_m_pos[0] < train.pos[0]+width and train.pos[1]-height-train.size[2] < localized_m_pos[1] < train.pos[1]+height:
                #pg.draw.rect(screen,(255,0,0),(train.pos[0]-width-player_pos[0]+screen_size[0]/2,train.pos[1]-height-player_pos[1]+screen_size[1]/2-train.size[2],width*2,height*2+train.size[2]))
                if mouse_clicked and m_btn[0]:
                    controlling = train_params[0]
                    controlling_consist = trains[controlling].consist
    ''' #временно без этого. оно не рабоатет с новой системой.
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



        panel = train_sprites[consists[controlling_consist].train_type]["controls"]["panel"]
        if (screen_size[0]/2+panel.get_width()/2 >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2 and 
            screen_size[1] >= m_pos[1] >= screen_size[1]-panel.get_height()):
            for elem_id, element in enumerate(consists[controlling_consist].consist_info["element_mapouts"]):
                if element["type"] != "analog_scale":
                    info = element["draw_mappings"][element["state"]]
                    x,y,w,h = info[0], info[1],info[4], info[5]
                    scale = info[2]
                    if element["type"] in ["button","switch"]:
                        if (screen_size[0]/2-panel.get_width()/2+x*scale+w*scale >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2+x*scale and 
                            screen_size[1]-panel.get_height()+y*scale+h*scale >= m_pos[1] >= screen_size[1]-panel.get_height()+y*scale): 
                            annotation = annotation_font.render(element["name"],True,(255,255,255))
                        if (screen_size[0]/2-panel.get_width()/2+x*scale+w*scale >= m_pos[0] >= screen_size[0]/2-panel.get_width()/2+x*scale and 
                            screen_size[1]-panel.get_height()+y*scale+h*scale >= m_pos[1] >= screen_size[1]-panel.get_height()+y*scale and (m_btn[0] or mouse_clicked)):
                            if element["type"] == "button" and (m_btn[0] and element["state"] != element["default"] or mouse_clicked):
                                consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] = not(element["default"])
                                consists[controlling_consist].control_wires[element["connection"]] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                if mouse_clicked and len(element["draw_mappings"][element["state"]]) == 7:
                                    sounds[consists[controlling_consist].train_type][element["draw_mappings"][element["state"]][6]].play()
                            elif element["type"] == "switch" and mouse_clicked and not mouse_clicked_prev:
                                consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] = not(consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"])
                                consists[controlling_consist].control_wires[element["connection"]] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                if len(element["draw_mappings"][element["state"]]) == 7:
                                    sounds[consists[controlling_consist].train_type][element["draw_mappings"][consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]][6]].play()
                        else:
                            if element["type"] == "button":
                                if consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] != element["default"] and len(element["draw_mappings"][element["default"]]) == 7:
                                    sounds[consists[controlling_consist].train_type][element["draw_mappings"][element["default"]][6]].play()
                                consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"] = element["default"]
                                consists[controlling_consist].control_wires[element["connection"]] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
    else:
        pass
                    

                    

    if controlling != -1:
        panel = train_sprites[consists[controlling_consist].train_type]["controls"]["panel"]

        if "underlay_draw_params" in consists[controlling_consist].consist_info:
            underlay = train_sprites[consists[controlling_consist].train_type]["controls"]["underlay"]
            x,y,scale = consists[controlling_consist].consist_info["underlay_draw_params"]
            screen.blit(underlay,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))

        
        rr_direction = int(consists[controlling_consist].controlling_direction*(1-2*trains[controlling].reversed))
        rr = train_sprites[consists[controlling_consist].train_type]["controls"][f"rr_{rr_direction}"]
        x,y = consists[controlling_consist].consist_info["rr_draw_mapouts"][str(rr_direction)]
        scale = consists[controlling_consist].consist_info["rr_draw_mapouts"]["scale"]
        screen.blit(rr,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))

        screen.blit(panel,(screen_size[0]/2-panel.get_width()/2,screen_size[1]-panel.get_height()))

        for element in consists[controlling_consist].consist_info["element_mapouts"]:
            if element["type"] != "analog_scale":
                info = element["draw_mappings"][element["state"]]
                sprite = train_sprites[consists[controlling_consist].train_type]["controls"][info[3]] 
                x,y = info[0], info[1]
                scale = info[2]
                screen.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
            else:
                info = element["draw_mappings"][0]
                sprite = train_sprites[consists[controlling_consist].train_type]["controls"][info[3]] 
                x,y = info[0], info[1]
                scale = info[2]
                screen.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
                
                info = element["draw_mappings"][1]
                sprite = pg.transform.rotate(train_sprites[consists[controlling_consist].train_type]["controls"][info[3]],round(element["base_angle"]-element["multiplier"]*element["angle"],5))
                local_x,local_y = info[0], info[1]
                local_scale = info[2]
                screen.blit(sprite,(round(screen_size[0]/2-panel.get_width()/2+(x*scale+local_x*local_scale)-sprite.get_width()/2,2),float(screen_size[1]-panel.get_height()+(int(y*scale+local_y*local_scale)+0.5)-sprite.get_height()/2)))

                info = element["draw_mappings"][2]
                sprite = train_sprites[consists[controlling_consist].train_type]["controls"][info[3]] 
                x,y = info[0], info[1]
                scale = info[2]
                screen.blit(sprite,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))


        km = train_sprites[consists[controlling_consist].train_type]["controls"]["km"]
        x,y = consists[controlling_consist].consist_info["km_draw_mapouts"][str(consists[controlling_consist].km)]
        scale = consists[controlling_consist].consist_info["km_draw_mapouts"]["scale"]
        screen.blit(km,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
        
        tk = train_sprites[consists[controlling_consist].train_type]["controls"]["tk"]
        x,y = consists[controlling_consist].consist_info["tk_draw_mapouts"][str(consists[controlling_consist].tk)]
        scale = consists[controlling_consist].consist_info["tk_draw_mapouts"]["scale"]
        screen.blit(tk,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))
        
        overlay = train_sprites[consists[controlling_consist].train_type]["controls"]["overlay"]
        screen.blit(overlay,(screen_size[0]/2-overlay.get_width()/2,screen_size[1]-overlay.get_height()))

        if annotation:
            s = pg.Surface((annotation.get_width()+8,annotation.get_height()+8))
            s.set_alpha(128)
            s.fill((0,0,0))
            screen.blit(s, (m_pos[0]+10,m_pos[1]+20))
            screen.blit(annotation, (m_pos[0]+15,m_pos[1]+25))

    if pg.K_TAB in keydowns:
        if controlling == -1:
            controlling = list(sorted(dict(trains).keys()))[0]
            controlling_consist = trains[controlling].consist
        else:
            controlling = list(sorted(dict(trains).keys()))[(list(sorted(dict(trains).keys())).index(controlling)+1)%len(trains)]
            controlling_consist = trains[controlling].consist            

    if controlling == -1:
        speed = 8 if pressed[pg.K_RSHIFT] or pressed[pg.K_LSHIFT] else 2
        if pressed[pg.K_DOWN]: 
            player_pos[1]+=speed*clock.get_fps()/60
        if pressed[pg.K_UP]: 
            player_pos[1]-=speed*clock.get_fps()/60
        if pressed[pg.K_LEFT]: 
            player_pos[0]-=speed*clock.get_fps()/60
        if pressed[pg.K_RIGHT]: 
            player_pos[0]+=speed*clock.get_fps()/60   
    else:
        player_pos = [trains[controlling].pos[0],trains[controlling].pos[1]-screen_size[1]/8*2*(1 if 90 <= (trains[controlling].angle+trains[controlling].reversed*180)%360 <= 270 else -1)]
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
    text_color = (200,200,200)
    info_blit_list.append(font.render("alphen's subway simulator "+version,True,text_color))
    info_blit_list.append(font.render("fps: "+str(int(clock.get_fps())), False, ((255 if clock.get_fps() < 45 else 0), (255 if clock.get_fps() > 15 else 0), 0)))
    if debug > 0:
        info_blit_list.append(font.render(f"tramcars: {len(trains)}",True,text_color))
        info_blit_list.append(font.render(f"consists: {len(consists)}",True,text_color))
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
            info_blit_list.append(font.render(f"RP {consists[controlling_consist].control_wires["rp"]}",True,text_color))
            info_blit_list.append(font.render(f"vz1 {consists[controlling_consist].control_wires["vz_1"]}",True,text_color))
            if debug > 1:
                info_blit_list.append(font.render(f"reverser {consists[controlling_consist].controlling_direction}",True,text_color))
                info_blit_list.append(font.render(f"traction {consists[controlling_consist].traction_direction}",True,text_color))
                info_blit_list.append(font.render(f"movement {consists[controlling_consist].velocity_direction}",True,text_color))
            

    for i, line in enumerate(info_blit_list):
            screen.blit(line, (0, 20*i))

    pg.display.update()
    clock.tick(60)
    if not working:
        pg.quit()