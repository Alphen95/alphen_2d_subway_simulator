import pygame as pg
import os
import json
import pathlib

version = "v0.1.4 первая очередь Строительная-Белогорская"
scale = 1
CURRENT_DIRECTORY = pathlib.Path(__file__).parent.resolve()
current_dir = CURRENT_DIRECTORY

from train import *



player_pos = [0,0]
block_pos = [0,0]
block_size = (256,1024)
screen_size = (1920,1080)
working = True
controlling = -1
following = -1
debug = 0

pg.init()
clock = pg.time.Clock()
screen = pg.display.set_mode((1920, 1080), )
pg.display.set_caption(f"Alphen's Subway Simulator v{version}")
font = pg.font.Font(os.path.join(CURRENT_DIRECTORY,"res","verdana.ttf"),20)

sprite_loading_info = [
    {"name":"tstr","filename":"tracks","params":[0,0,64,256,0,False,False]},
    {"name":"tca1","filename":"tracks","params":[64,0,64,256,0,False,False]},
    {"name":"tca2","filename":"tracks","params":[128,0,64,256,0,False,False]},
    {"name":"tcb1","filename":"tracks","params":[64,0,64,256,0,True,False]},
    {"name":"tcb2","filename":"tracks","params":[128,0,64,256,0,True,False]},
    {"name":"tsa1","filename":"tracks","params":[192,0,64,256,0,False,False]},
    {"name":"tsa2","filename":"tracks","params":[256,0,64,256,0,False,False]},
    {"name":"tsb1","filename":"tracks","params":[192,0,64,256,0,True,False]},
    {"name":"tsb2","filename":"tracks","params":[256,0,64,256,0,True,False]},
    {"name":"eto_platforma","filename":"platform","params":[0,0,64,256,0,False,False]},
    {"name":"barekamutyn_track_l_tstr","filename":"platform","params":[64,0,64,256,0,False,False]},
    {"name":"barekamutyn_track_r_tstr","filename":"platform","params":[64,0,64,256,0,True,False]},
    {"name":"barekamutyn_platform_l","filename":"platform","params":[128,0,64,256,0,False,False]},
    {"name":"barekamutyn_platform_r","filename":"platform","params":[128,0,64,256,0,True,False]},
    {"name":"tozolosh_track_l_tstr","filename":"platform","params":[64*4,0,64,256,0,False,False]},
    {"name":"tozolosh_track_r_tstr","filename":"platform","params":[64*4,0,64,256,0,True,False]},
    {"name":"tozolosh_platform_l","filename":"platform","params":[64*3,0,64,256,0,False,False]},
    {"name":"tozolosh_platform_r","filename":"platform","params":[64*3,0,64,256,0,True,False]},
    {"name":"aktau_track_l_tstr","filename":"platform","params":[64*6,0,64,256,0,False,False]},
    {"name":"aktau_track_r_tstr","filename":"platform","params":[64*6,0,64,256,0,True,False]},
    {"name":"aktau_platform_l","filename":"platform","params":[64*5,0,64,256,0,False,False]},
    {"name":"aktau_platform_r","filename":"platform","params":[64*5,0,64,256,0,True,False]},
]
ground_sprites = {}

temp_sprites = {}
filenames = os.listdir(os.path.join(CURRENT_DIRECTORY,"res"))
for filename in filenames:
    if filename[-4:] == ".png":
        temp_sprites[filename[:-4]] = pg.image.load(os.path.join(*([current_dir,"res",filename]))).convert_alpha()

for info_pack in sprite_loading_info:
    ground_sprites[info_pack["name"]] = pg.transform.rotate(
        pg.transform.flip(
            temp_sprites[info_pack["filename"]].subsurface(*info_pack["params"][:4]),
            info_pack["params"][5],info_pack["params"][6]
        ),
        info_pack["params"][4]
    )

train_sprites = {}
train_types = {}
consists_info = {}

train_folders = os.listdir(os.path.join(current_dir,"trains"))
for folder in train_folders:
    folder_contents = os.listdir(os.path.join(current_dir,"trains",folder))
    if "train.json" in folder_contents:
        
        with open(os.path.join(CURRENT_DIRECTORY,"trains",folder,"train.json")) as file:
            train_parameters = json.loads(file.read())
            base_train_sprite = pg.image.load(os.path.join(*([current_dir,"trains",folder,"sprite.png"]))).convert_alpha()
            base_control_panel_sprite = pg.image.load(os.path.join(*([current_dir,"trains",folder,"controls.png"]))).convert_alpha()
            key = train_parameters["system_name"]
            train_sprites[key] = {}
            consists_info[key] = train_parameters["traction_info"]
            base_layers = []
            sprite_stack_factor = 3

            sprite_params = train_parameters["sprite_info"]["train"]

            for i in range(sprite_params["layers"]):
                x_pos = sprite_params["w"]*i# if not ("reversed" in sprite_params and sprite_params["reversed"]) else sprite_params["h_layer"]*(sprite_params["layer_amount"]-1-i)
                base_layers.append(pg.transform.scale(base_train_sprite.subsurface(x_pos,0,sprite_params["w"],sprite_params["h"]),(sprite_params["w"]*4,sprite_params["h"]*4)))


            for rotation in [*range(0,360,5)]+[8.25,16.5,360-8.25,360-16.5,180-8.25,180-16.5,180+8.25,180+16.5]:
                w, h = pg.transform.rotate(base_layers[0],rotation).get_size()

                surface = pg.Surface((w,h+sprite_params["layers"]*sprite_stack_factor-1))
                surface.set_colorkey((0,0,0))

                for i in range(sprite_params["layers"]*sprite_stack_factor):
                    pos = (0,surface.get_height()-i-h)
                    surface.blit(pg.transform.rotate(base_layers[int(i/sprite_stack_factor)],rotation),pos)
                train_sprites[key][rotation] = surface
            train_sprites[key]["height"] = sprite_params["layers"]*sprite_stack_factor-1


            controls_info = train_parameters["control_panel_info"]
            train_sprites[key]["controls"] = {}
            train_sprites[key]["controls"]["panel"] = pg.transform.scale(
                base_control_panel_sprite.subsurface(controls_info["panel"]["x"],controls_info["panel"]["y"],controls_info["panel"]["w"],controls_info["panel"]["h"]),
                (controls_info["panel"]["w"]*controls_info["panel"]["scale"],controls_info["panel"]["h"]*controls_info["panel"]["scale"]))
            
            train_sprites[key]["controls"]["km"] = pg.transform.scale(
                base_control_panel_sprite.subsurface(controls_info["km"]["x"],controls_info["km"]["y"],controls_info["km"]["w"],controls_info["km"]["h"]),
                (controls_info["km"]["w"]*controls_info["km"]["scale"],controls_info["km"]["h"]*controls_info["km"]["scale"]))
            
            train_sprites[key]["controls"]["tk"] = pg.transform.scale(
                base_control_panel_sprite.subsurface(controls_info["tk"]["x"],controls_info["tk"]["y"],controls_info["tk"]["w"],controls_info["tk"]["h"]),
                (controls_info["tk"]["w"]*controls_info["tk"]["scale"],controls_info["tk"]["h"]*controls_info["tk"]["scale"]))
            
            train_sprites[key]["controls"]["rr"] = {}

            train_sprites[key]["controls"]["rr"][1] = pg.transform.scale(
                base_control_panel_sprite.subsurface(controls_info["rr_1"]["x"],controls_info["rr_1"]["y"],controls_info["rr_1"]["w"],controls_info["rr_1"]["h"]),
                (controls_info["rr_1"]["w"]*controls_info["rr_1"]["scale"],controls_info["rr_1"]["h"]*controls_info["rr_1"]["scale"]))
            
            train_sprites[key]["controls"]["rr"][0] = pg.transform.scale(
                base_control_panel_sprite.subsurface(controls_info["rr_0"]["x"],controls_info["rr_0"]["y"],controls_info["rr_0"]["w"],controls_info["rr_0"]["h"]),
                (controls_info["rr_0"]["w"]*controls_info["rr_0"]["scale"],controls_info["rr_0"]["h"]*controls_info["rr_0"]["scale"]))
            
            train_sprites[key]["controls"]["rr"][-1] = pg.transform.scale(
                base_control_panel_sprite.subsurface(controls_info["rr_-1"]["x"],controls_info["rr_-1"]["y"],controls_info["rr_-1"]["w"],controls_info["rr_-1"]["h"]),
                (controls_info["rr_-1"]["w"]*controls_info["rr_-1"]["scale"],controls_info["rr_-1"]["h"]*controls_info["rr_-1"]["scale"]))
            
            train_sprites[key]["controls"]["overlay"] = pg.transform.scale(
                base_control_panel_sprite.subsurface(controls_info["overlay"]["x"],controls_info["overlay"]["y"],controls_info["overlay"]["w"],controls_info["overlay"]["h"]),
                (controls_info["overlay"]["w"]*controls_info["overlay"]["scale"],controls_info["overlay"]["h"]*controls_info["overlay"]["scale"]))

            train_types[key] = {}
            train_types[key]["size"] = (*train_parameters["clickable_size"],sprite_params["layers"]*sprite_stack_factor-1)


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
switches = {
    (0,1):False,
    (0,-10):True,
    (-1,-10):True
}

#trains = {}
consists = {}
consist_key = random.randint(0,999)
consists[consist_key] = Consist("type_a",train_types["type_a"],consists_info["type_a"],consist_key,world,[256*0.5,1024*2.5])

player_pos = [256*0.5,1024*2.5]

while working:
    valid = []
    valid_draw = []
    for train_id in trains:
        train = trains[train_id]
        if (player_pos[0]-screen_size[0] <= train.pos[0] <= player_pos[0]+screen_size[0]) and (player_pos[1]-screen_size[1] <= train.pos[1] <= player_pos[1]+screen_size[1]):
            valid.append([train_id,train.pos[1]])
            valid_draw.append([(train.pos[0],train.pos[1]),train.type,train.angle,train.reversed])
    if controlling != -1: player_pos = [trains[controlling].pos[0],trains[controlling].pos[1]-screen_size[1]/8*2*(1 if 90 <= (trains[controlling].angle+trains[controlling].reversed*180)%360 <= 270 else -1)]
    block_pos = [int((player_pos[0]-(block_size[0] if player_pos[0] < 0 else 0))/block_size[0]),int((player_pos[1]-(block_size[1] if player_pos[1] < 0 else 0))/block_size[1])]

    keydowns = []
    mouse_clicked = False
    for evt in pg.event.get():
        if evt.type == pg.QUIT:
            working = False
        if evt.type == pg.KEYDOWN:
            keydowns.append(evt.key)
            if evt.key == pg.K_d:
                debug = (debug+1)%3
        if evt.type == pg.MOUSEBUTTONDOWN:
            mouse_clicked = True

    screen.fill((25,25,25))
    for tile_y in range(-int(screen_size[1]/block_size[1]/2)-1,int(screen_size[1]/block_size[1]/2)+2):
        for tile_x in range(-int(screen_size[0]/block_size[0]/2)-1,int(screen_size[0]/block_size[0]/2)+2):
            #pg.draw.rect(screen,(255,0,0),)
            if (block_pos[0]+tile_x,block_pos[1]+tile_y) in world:
                tile_world_position = (block_pos[0]+tile_x,block_pos[1]+tile_y)

                if world[tile_world_position] in ground_sprites:
                    screen.blit(pg.transform.scale(ground_sprites[world[tile_world_position]],block_size),(
                        screen_size[0]/2+tile_x*block_size[0]-player_pos[0]%(block_size[0]),
                        screen_size[1]/2+tile_y*block_size[1]-player_pos[1]%(block_size[1])
                    ))
    for i, train_params in enumerate(sorted(valid_draw,key=lambda x:x[1])):
        
        angle = (valid_draw[i][2]+valid_draw[i][3]*180)%360 if valid_draw[i][2] in train_sprites[valid_draw[i][1]] else (valid_draw[i][2]+valid_draw[i][3]*180)//5*5
        sprite = train_sprites[train.type][angle]
        screen.blit(
            sprite,
            (
                -player_pos[0]+valid_draw[i][0][0]+screen_size[0]/2-sprite.get_width()/2,
                -player_pos[1]+valid_draw[i][0][1]+screen_size[1]/2-sprite.get_height()/2-train_sprites[valid_draw[i][1]]["height"]/2
            )
        )
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

    
    for train_params in sorted(valid,key=lambda x:x[1]):
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
    if controlling != -1:
        panel = train_sprites[consists[controlling_consist].train_type]["controls"]["panel"]
        
        rr_direction = int(consists[controlling_consist].controlling_direction*(1-2*trains[controlling].reversed))
        rr = train_sprites[consists[controlling_consist].train_type]["controls"]["rr"][rr_direction]
        x,y = consists[controlling_consist].consist_info["rr_draw_mapouts"][str(rr_direction)]
        scale = consists[controlling_consist].consist_info["rr_draw_mapouts"]["scale"]
        screen.blit(rr,(screen_size[0]/2-panel.get_width()/2+x*scale,screen_size[1]-panel.get_height()+y*scale))

        screen.blit(panel,(screen_size[0]/2-panel.get_width()/2,screen_size[1]-panel.get_height()))

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
            info_blit_list.append(font.render(f"velocity {round(consists[controlling_consist].velocity,5)} px",True,text_color))
            info_blit_list.append(font.render(f"velocity {round(consists[controlling_consist].humainzed_velocity,2)} m/s",True,text_color))
            info_blit_list.append(font.render(f"velocity {round(consists[controlling_consist].humainzed_velocity*3.6,2)} km/h",True,text_color))
            info_blit_list.append(font.render(f"pressure {round(consists[controlling_consist].pressure)} aT",True,text_color))
            info_blit_list.append(font.render(f"km {consists[controlling_consist].km}",True,text_color))
            info_blit_list.append(font.render(f"tk {consists[controlling_consist].tk}",True,text_color))
            info_blit_list.append(font.render(f"energy {consists[controlling_consist].energy}",True,text_color))
            info_blit_list.append(font.render(f"emf {consists[controlling_consist].electromotive_force}",True,text_color))
            info_blit_list.append(font.render(f"volts {consists[controlling_consist].engine_voltage}",True,text_color))
            info_blit_list.append(font.render(f"reverser {consists[controlling_consist].controlling_direction}",True,text_color))
            info_blit_list.append(font.render(f"traction {consists[controlling_consist].traction_direction}",True,text_color))
            info_blit_list.append(font.render(f"movement {consists[controlling_consist].velocity_direction}",True,text_color))
            

    for i, line in enumerate(info_blit_list):
            screen.blit(line, (0, 20*i))

    pg.display.update()
    clock.tick(60)
    if not working:
        pg.quit()