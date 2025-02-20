import pygame as pg
import os
import json
import math

pg.init()
sprite_stack_factor = 4
compression = 2
world_angle = 45
train_angles = [world_angle,world_angle+180]+[14+world_angle,-14+world_angle,180-14+world_angle,180+14+world_angle]

#clock = pg.time.Clock()

#шняга утилита для пререндера паков (грузить должно быстрее поидее)
#надо это будет закинуть в редачер

#так как это мой код, я волен писать здесь любую ахинею
#ну и душу поизливать можно вроде
#ну так вот
#эта вся щняга - мегахуйня, НО
#оптимизировать основную треду ещё хуже
#если это вообще кто-то читает и играет в мою хуйню - зур-рахмат, ото всей души
packs = os.listdir(os.path.join("paks"))
print("choose a pack and type its number or type 0 to exit.")
for i,pack in enumerate(packs):
    print(i+1,pack)
pack_id = input(">")
if pack_id != "0" and int(pack_id) <= len(packs):
    pack_name = packs[int(pack_id)-1]

    if os.path.isdir(f"paks/{pack_name}"):
        folder_contents = os.listdir(os.path.join("paks",pack_name))
        if "pack.json" in folder_contents:
            print("found the pack. strap yourself, it could take a while.")

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
                    for info_pack in pack_parameters["tiles"]:
                        base_ground_sprite = temp_sprites[info_pack["filename"]].subsurface(info_pack["params"][0],info_pack["params"][1],info_pack["params"][2]*info_pack["params"][4],info_pack["params"][3])
                        #base_ground_sprite.set_colorkey((0,0,0))
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
                        #sterletomak_asset_pack
                        '''w, h = pg.transform.rotate(
                            base_layers[0].subsurface(
                                0,
                                base_layers[0].get_height()/4,
                                base_layers[0].get_width(),
                                base_layers[0].get_height()/4
                            ),rotation).get_size()
                        h=h/compression
                        h+=(info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor
                        dx = (surface.get_width()-w)/3
                        dy = (surface.get_height()-h)/3
                        for q in range(4):
                            print(q)
                            surf = surface.subsurface((dx*q,dy*q,w,h))
                            pg.image.save(surf,os.path.join("paks",pack_name,"render",f"{info_pack['name']}_{q}.png"))
                        ''' #ОНО РАБОТАЕТ, но на кой оно нужно, когда есть полноценыш?

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

                            #surface = pg.transform.scale(surface,(surface.get_width(),surface.get_height()/2))

                            pg.image.save(surface,os.path.join("paks",pack_name,"render",f"{info_pack['name']}_{q}.png"))
                        rendered_info["tiles"].append([info_pack['name'],(info_pack["params"][4]+info_pack["params"][5])*sprite_stack_factor-1])
                        print("rendered",info_pack['name'])
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
                                pg.image.save(global_l_surface,os.path.join("paks",pack_name,"render",f"{key}_{door_type}_{rotation}_l.png"))
                                pg.image.save(global_r_surface,os.path.join("paks",pack_name,"render",f"{key}_{door_type}_{rotation}_r.png"))
                            rendered_info["trains"].append([key,door_type,sprite_params["layers"]*sprite_stack_factor-1,train_parameters["designed_for"],train_parameters["name"]])
            pack_parameters["rendered"] = rendered_info
            with open(os.path.join("paks",pack_name,"pack.json"),encoding="utf-8",mode="w") as file:
                json.dump(pack_parameters, file, ensure_ascii=False, sort_keys=True,indent=4)

        else:
            print("no pack.json in your pack")
    else:
        print("no such pack")