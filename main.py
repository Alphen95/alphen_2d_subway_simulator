import pygame as pg
import os
import json
import math
import time
import threading
import random
import pathlib

version = "0.4.3 перегонка на формат с возможностью компиляции"
version_id = version.split(" ")[0]
scale = 1
CURRENT_DIRECTORY = ""
current_dir = CURRENT_DIRECTORY
#directory deprecated 11-11-24 to work with cxFreeze and be able to use non-packed gamedata

#from train import *
#Train module deprecated and merged with main 11-11-24

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
screen = pg.display.set_mode(screen_size, pg.SRCALPHA)
pg.display.set_caption(f"Alphen's 2.5D Subway Simulator v{version_id}")
screen_state = "loading"

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
    {"name":"sodovaya_walls_f","filename":"platform","params":[64*3,256*5,64,256,29,3,True,False]},
    {"name":"sodovaya_platform_f","filename":"platform","params":[0,256*5,64,256,3,0,True,False]},
    {"name":"sodovaya_track_tstr","filename":"platform","params":[0,256*6,64,256,32,0,False,False]},
    {"name":"sodovaya_track_f_tstr","filename":"platform","params":[0,256*6,64,256,3,0,True,False]},

    {"name":"kochetova_walls","filename":"platform","params":[64*3,256*7,64,256,29,3,False,False]},
    {"name":"kochetova_platform","filename":"platform","params":[0,256*7,64,256,3,0,False,False]},
    {"name":"kochetova_track_tstr","filename":"platform","params":[0,256*8,64,256,32,0,False,False]},
    {"name":"kochetova_walls_f","filename":"platform","params":[64*3,256*7,64,256,29,3,True,False]},
    {"name":"kochetova_platform_f","filename":"platform","params":[0,256*7,64,256,3,0,True,False]},
    {"name":"kochetova_track_f_tstr","filename":"platform","params":[0,256*8,64,256,3,0,True,False]},

    {"name":"park_kultury_walls","filename":"platform","params":[64*3,256*9,64,256,29,3,False,False]},
    {"name":"park_kultury_platform","filename":"platform","params":[0,256*9,64,256,3,0,False,False]},
    {"name":"park_kultury_track_tstr","filename":"platform","params":[0,256*10,64,256,32,0,False,False]},
    {"name":"park_kultury_walls_f","filename":"platform","params":[64*3,256*9,64,256,29,3,True,False]},
    {"name":"park_kultury_platform_f","filename":"platform","params":[0,256*9,64,256,3,0,True,False]},
    {"name":"park_kultury_track_f_tstr","filename":"platform","params":[0,256*10,64,256,3,0,True,False]},
]
ground_sprites = {}
train_sprites = {}
train_types = {}
sounds = {}
consists_info = {}
consists = {}
progress = 0

pg.mixer.init()
channel_rolling = pg.mixer.Channel(1)
channel_rolling.set_volume(0.125)
train_folders = os.listdir(os.path.join(current_dir,"trains"))

trains = {}

sign = lambda x: math.copysign(1, x)

class Train():
    def __init__(self,pos,type, reversed,size,consist,world):
        self.pos = pos
        self.type = type
        self.velocity = 0
        self.angle = 180
        self.reversed = reversed
        self.size = size
        self.consist = consist

        self.exists = True
        self.thread = threading.Thread(target=self.cycle,args=[world],daemon=True)
        self.thread.start()
        self.switches = []

    def cycle(self,world):
        block_size = (256,1024)


        while self.exists:
            block_pos = (int((self.pos[0]-(block_size[0] if self.pos[0] < 0 else 0))/block_size[0]),int((self.pos[1]-(block_size[1] if self.pos[1] < 0 else 0))/block_size[1]))
            local_pos = (self.pos[0]%block_size[0],self.pos[1]%block_size[1])

            if block_pos in world:

                curblock = world[block_pos][0] if type(world[block_pos]) == list else world[block_pos]
                if curblock[-4:] == "tstr":
                    self.angle = 180 if 270 >= self.angle >= 90 else 0
                    if local_pos[0] < 127.95:
                        self.pos[0] += 0.05
                    elif local_pos[0] > 128.05:
                        self.pos[0] -= 0.05
                    
                    if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                        self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tca1":
                    if local_pos[1] > 4*(256-39):
                        self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                    else:
                        self.angle = 180-16.5 if 270 >= self.angle >= 90 else 16.5
                elif curblock[-4:] == "tca2":
                    if local_pos[1] < 4*(39):
                        self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                    else:
                        self.angle = 180-16.5 if 270 >= self.angle >= 90 else 16.5
                elif curblock[-4:] == "tcb1":
                    if local_pos[1] > 4*(256-39):
                        self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                    else:
                        self.angle = 180+16.5 if 270 >= self.angle >= 90 else 360-16.5
                elif curblock[-4:] == "tcb2":
                    if local_pos[1] < 4*(39):
                        self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                    else:
                        self.angle = 180+16.5  if 270 >= self.angle >= 90 else 360-16.5
                
                elif curblock[-4:] == "tsa1":
                    if int(self.angle) not in [0,180] or ((local_pos[1] > 4*(256-2) or local_pos[1] < 4*64) and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] > 4*(256-39):
                            self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                        elif local_pos[1] > 4*64:
                            self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                        else:
                            self.angle = 180 if 270 >= self.angle >= 90 else 0
                    else:
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsa2":
                    if self.angle not in [0,180] or ((local_pos[1] < 4*(2) or local_pos[1] > 4*(64*3)) and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] < 4*(39):
                            self.angle = 180-8.25 if 270 >= self.angle >= 90 else 8.25
                        elif local_pos[1] < 4*(64*3):
                            self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                        else:
                            self.angle = 180 if 270 >= self.angle >= 90 else 0
                    else:
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsb1":
                    if int(self.angle) not in [0,180] or ((local_pos[1] > 4*(256-2) or local_pos[1] < 4*64) and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] > 4*(256-39):
                            self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                        elif local_pos[1] > 4*64:
                            self.angle = 180+16.5 if 270 >= self.angle >= 90 else 360-16.5
                        else:
                            self.angle = 180 if 270 >= self.angle >= 90 else 0
                    else:
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsb2":
                    if self.angle not in [0,180] or ((local_pos[1] < 4*(2) or local_pos[1] > 4*(64*3)) and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] < 4*(39):
                            self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                        elif local_pos[1] < 4*(64*3):
                            self.angle = 180+16.5  if 270 >= self.angle >= 90 else 360-16.5
                        else:
                            self.angle = 180 if 270 >= self.angle >= 90 else 0
                    else:
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]

            
            
            time.sleep(1/120)

class Consist():
    def __init__(self,train_type,params,consist_info,self_id,world,spawn_pos):
        global trains

        self.linked_to = []
        self.pressure = 0
        self.vz_pressure = 0
        self.velocity = 0
        self.pixel_velocity = 0
        self.angular_velocity = 0
        self.train_type = train_type
        self.wheel_radius = consist_info["wheel_radius"]
        self.mass = consist_info["mass"]
        self.wheel_mass = consist_info["wheel_mass"]
        self.humainzed_velocity = 0
        self.current_roll_sound = -1

        self.control_wires ={
            "main_power":False, #1 Главный разъединитель и главный автомат
            "reserve_controls":False, #1 Резервное управление
            "batteries":False, #2 Питание батарей
            "mk":False, #3 Питание мотор-компрессора
            "reserve_mk":False, #4 Питание резервного мотор-компрессора
            "reversor_forwards":False, #5 Реверс вперёд
            "reversor_backwards":False, #6 Реверс назад
            "rp":True, #7 Реле перегрузки (False = требует восстановки)
            "rp_return":False, #8 Возврат реле перегрузки
            "vz_1":False, #9 Вентиль замещения №1
            "vz_2":False, #10 Вентиль замещения №2
            "traction":False, #11 Сбор схемы на ход
            "electro_brake":False, #12 Сбор схемы на торможение
            "maximal_traction":False, #13 Сбор схемы на максимальный ход
            "rk_spin":False, #14 Вращение реостатного контроллера
            "rk_maxed":False, #15 Схема собрана (РК на максимальной допустимой позиции)
            "left_doors":False, #16 Открытие левых дверей
            "right_doors":False, #17 Открытие правых дверей
            "close_doors":False, #18 Закрытие дверей
            "reserve_close_doors":False, #19 Резервное закрытие дверей
            "doors_open":False, #20 Двери открыты
            "doors_open_duplicate":False, #21 Двери открыты
            "light_on":False, #22 Включение освещения
            "light_off":False, #23 Выключение освещения
            "ars":False, #24 Включение АРС
            "als":False, #25 Включение АЛС
            "ars_0":False, #26 АРС - 0
            "ars_20":False, #27 АРС - НЧ [20]
            "ars_40":False, #28 АРС - 40
            "ars_60":False, #29 АРС - 60
            "ars_70":False, #30 АРС - 70
            "ars_80":False, #31 АРС - 80
            "unused":False, #32 пока не используется

        }
        self.consist_info = consist_info
        self.doors = {
            "l":"closed",
            "r":"closed",
            "timer_l":0,
            "timer_r":0,
            "action_l":None,
            "action_r":None,
        }

        self.km = consist_info["default_km"]
        self.tk = consist_info["default_tk"]

        self.energy = 0
        self.engine_voltage = 0
        self.engine_current = 0
        self.electromotive_force = 0
        self.vz_1 = 0
        self.vz_2 = 0
        self.engine_constant = consist_info["engine_constant"]
        self.engine_resistance = consist_info["engine_resistance"]
        self.transmissional_number = consist_info["transmissional_number"]
        self.break_cyllinder_surface = consist_info["break_cyllinder_surface"]

        self.controlling_direction = 0
        self.traction_direction = 0
        self.velocity_direction = 0

        pos = spawn_pos
        self.train_amount = 3
        for i in range(self.train_amount):
            train_id = random.randint(0,99999)
            trains[train_id] = Train([pos[0],pos[1]+320*i],train_type, i+1==self.train_amount,params["size"],self_id,world)
            self.linked_to.append(train_id)

        self.exists = True
        self.thread = threading.Thread(target=self.cycle,daemon=True) #,args=[world]
        self.thread.start()

    def cycle(self):
        global trains
        pi = 3.1415
        wheels = 8*self.train_amount
        engines = 2*self.train_amount
        magical_proskalzyvanie_scale = 0.95 #на случай если движок больно резвый

        while self.exists:
            for elem_id, element in enumerate(self.consist_info["element_mapouts"]):
                if element["type"] == "lamp":
                    self.consist_info["element_mapouts"][elem_id]["state"] = self.control_wires[element["connection"]]
                elif element["type"] == "analog_scale":
                    value = 0
                    if element["scale"] == "velocity": value = self.velocity*3.6
                    elif element["scale"] == "amps": value = self.engine_current*self.traction_direction*self.control_wires["rp"]
                    elif element["scale"] == "volts": value = self.engine_voltage*self.control_wires["rp"]
                    elif element["scale"] == "press": value = max(self.vz_1,self.vz_2,self.pressure)

                    if value != element["angle"]:
                        self.consist_info["element_mapouts"][elem_id]["angle"] += (element["max_value"]-element["min_value"])/100*sign(value-element["angle"])
                        if self.consist_info["element_mapouts"][elem_id]["angle"] > element["max_value"]: self.consist_info["element_mapouts"][elem_id]["angle"] = element["max_value"]
                        elif self.consist_info["element_mapouts"][elem_id]["angle"] < element["min_value"]: self.consist_info["element_mapouts"][elem_id]["angle"] = element["min_value"]
                        elif abs(value-self.consist_info["element_mapouts"][elem_id]["angle"]) <(element["max_value"]-element["min_value"])/100: self.consist_info["element_mapouts"][elem_id]["angle"] = value


            if self.consist_info["control_system_type"] == "direct":
                if self.control_wires["rp_return"] and self.km == 0:
                    self.control_wires["rp"] = True
                if self.control_wires["right_doors"] and self.doors["r"] == "closed":
                    self.doors["action_r"] = "open"
                if self.control_wires["left_doors"] and self.doors["l"] == "closed":
                    self.doors["action_l"] = "open"
                if self.control_wires["close_doors"]:
                    self.doors["action_r"] = "close" if self.doors["r"] != "closed" else None
                    self.doors["action_l"] = "close" if self.doors["l"] != "closed" else None
                self.control_wires["doors_open"] = self.doors["r"] != "closed" or self.doors["l"] != "closed"

                if self.doors["action_r"] == "open":
                    z = list(self.consist_info["door_animation_states"].keys())
                    if self.doors["timer_r"] == 0:
                        self.doors["r"] = z[z.index(self.doors["r"])+1]
                        if self.doors["r"] != "open":
                            self.doors["timer_r"] = self.consist_info["door_animation_states"][self.doors["r"]]
                        else:
                            self.doors["action_r"] = None
                    if self.doors["timer_r"] > 0: self.doors["timer_r"] -= 1
                elif self.doors["action_r"] == "close":
                    z = list(self.consist_info["door_animation_states"].keys())
                    if self.doors["timer_r"] == 0:
                        self.doors["r"] = z[z.index(self.doors["r"])-1]
                        if self.doors["r"] != "closed":
                            self.doors["timer_r"] = self.consist_info["door_animation_states"][self.doors["r"]]
                        else:
                            self.doors["action_r"] = None
                    if self.doors["timer_r"] > 0: self.doors["timer_r"] -= 1

                if self.doors["action_l"] == "open":
                    z = list(self.consist_info["door_animation_states"].keys())
                    if self.doors["timer_l"] == 0:
                        self.doors["l"] = z[z.index(self.doors["l"])+1]
                        if self.doors["l"] != "open":
                            self.doors["timer_l"] = self.consist_info["door_animation_states"][self.doors["l"]]
                        else:
                            self.doors["action_l"] = None
                    if self.doors["timer_l"] > 0: self.doors["timer_l"] -= 1
                elif self.doors["action_l"] == "close":
                    z = list(self.consist_info["door_animation_states"].keys())
                    if self.doors["timer_l"] == 0:
                        self.doors["l"] = z[z.index(self.doors["l"])-1]
                        if self.doors["l"] != "closed":
                            self.doors["timer_l"] = self.consist_info["door_animation_states"][self.doors["l"]]
                        else:
                            self.doors["action_l"] = None
                    if self.doors["timer_l"] > 0: self.doors["timer_l"] -= 1

                self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi*self.transmissional_number
                engine_power = 0
                if self.consist_info["km_mapouts"][str(self.km)]["type"] == "accel" and self.controlling_direction != 0 and self.control_wires["rp"]:
                    self.engine_voltage = self.consist_info["km_mapouts"][str(self.km)]["voltage"]
                    self.traction_direction = self.controlling_direction*sign(self.engine_voltage)
                    if self.velocity_direction == 0: 
                        self.velocity_direction = self.traction_direction
                    self.engine_current = (abs(self.engine_voltage)-(self.electromotive_force*(1 if self.traction_direction == self.velocity_direction else -1)))/self.engine_resistance
                    if self.engine_current <= 0: self.engine_current = 0
                    if self.engine_current >= self.consist_info["peril_current"]:
                        self.control_wires["rp"] = False
                        self.engine_current = 0
                        self.engine_voltage = 0
                    engine_power = abs(self.engine_voltage)*self.engine_current*(self.velocity_direction*self.traction_direction) if self.engine_current > 0 and self.control_wires["rp"] else 0
                
                self.vz_1 = (self.vz_1 + (2*self.control_wires["vz_1"]-1)*self.consist_info["valve_params"]["vz_1"][1]) 
                self.vz_1 = (self.vz_1 if self.vz_1 >= 0 else 0)
                self.vz_1 = (self.vz_1 if self.vz_1 <= self.consist_info["valve_params"]["vz_1"][0] else self.consist_info["valve_params"]["vz_1"][0])

                if self.consist_info["tk_mapouts"][str(self.tk)]["type"] == "press":
                    if self.pressure != self.consist_info["tk_mapouts"][str(self.tk)]["target"]:
                        if abs(self.pressure - self.consist_info["tk_mapouts"][str(self.tk)]["target"]) < self.consist_info["tk_mapouts"][str(self.tk)]["speed"]:
                            self.pressure = self.consist_info["tk_mapouts"][str(self.tk)]["target"]
                        else:
                            self.pressure+=-sign(self.pressure - self.consist_info["tk_mapouts"][str(self.tk)]["target"])*self.consist_info["tk_mapouts"][str(self.tk)]["speed"]

                self.control_wires["traction"] = engine_power > 0
                self.control_wires["maximal_traction"] = self.km == self.consist_info["max_km"]
                self.control_wires["reversor_forwards"] = self.controlling_direction == 1
                self.control_wires["reversor_backwards"] = self.controlling_direction == -1

                engine_power*=engines

                kinetic_energy = self.mass*(self.velocity**2)/2*self.train_amount
                revolutional_energy = self.wheel_mass*self.wheel_radius**2*self.angular_velocity**2/4*wheels
                friction_energy = 0.05*self.wheel_mass*9.81*self.angular_velocity
                break_friction_energy = wheels*1*self.velocity*(max(self.pressure,self.vz_1,self.vz_2)*100000*self.break_cyllinder_surface)

                self.energy = round(kinetic_energy+revolutional_energy+engine_power*self.transmissional_number/120-friction_energy/120-break_friction_energy/120,5)
                self.velocity = ((2*self.energy*self.wheel_radius**2)/(self.train_amount*self.mass*self.wheel_radius**2+wheels*self.wheel_mass*self.wheel_radius**2/2))**0.5
                self.velocity = round(complex(self.velocity).real,5)
                self.angular_velocity = round(self.velocity/self.wheel_radius,5)
                if self.velocity == 0: self.velocity_direction = 0


            speed_modifier = 1
            #self.humainzed_velocity = round(self.velocity*120*0.15/4*speed_modifier,5)
            self.pixel_velocity = round(self.velocity/120/0.15*4*speed_modifier,5)

            for train_id in self.linked_to:
                trains[train_id].velocity = self.velocity
                trains[train_id].pos[0]+=round(math.sin(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)
                trains[train_id].pos[1]+=round(math.cos(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)

            time.sleep(1/120)

def sprite_load_routine():
    global ground_sprites, train_sprites,train_types, sounds, consists_info,CURRENT_DIRECTORY,sprite_loading_info,screen_state,consists,progress,train_folders

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
        

    for folder in train_folders:
        folder_contents = os.listdir(os.path.join(current_dir,"trains",folder))
        if "train.json" in folder_contents:
            
            with open(os.path.join(CURRENT_DIRECTORY,"trains",folder,"train.json"),encoding="utf-8") as file:
                train_parameters = json.loads(file.read())
                base_train_sprite = pg.image.load(os.path.join(*([current_dir,"trains",folder,"sprite.png"]))).convert_alpha()
                base_control_panel_sprite = pg.image.load(os.path.join(*([current_dir,"trains",folder,"controls.png"]))).convert_alpha()
                key = train_parameters["system_name"]
                train_sprites[key] = {"controls":{},"doors":{}}
                consists_info[key] = train_parameters["traction_info"]
                sprite_stack_factor = 4

                for sprite_params in train_parameters["sprite_info"]:
                    base_layers = []
                    door_type = sprite_params["type"]
                    train_sprites[key]["doors"][door_type] = {"type":door_type}

                    for j in range(sprite_params["layers"]):
                        x_pos = sprite_params["w"]*j# if not ("reversed" in sprite_params and sprite_params["reversed"]) else sprite_params["h_layer"]*(sprite_params["layer_amount"]-1-i)
                        base_layers.append(pg.transform.scale(base_train_sprite.subsurface(x_pos,sprite_params["y"],sprite_params["w"],sprite_params["h"]),(sprite_params["w"]*4,sprite_params["h"]*4)))


                    for rotation in [0,180,world_angle,world_angle+180]+[8.25+world_angle,16.5+world_angle,-8.25+world_angle,-16.5+world_angle,180-8.25+world_angle,180-16.5+world_angle,180+8.25+world_angle,180+16.5+world_angle]:
                        w, h = pg.transform.rotate(base_layers[0],rotation).get_size()
                        h/=compression
                        rotation = rotation%360

                        global_l_surface = pg.Surface((w,h+sprite_params["layers"]*sprite_stack_factor-1))
                        global_r_surface = pg.Surface((w,h+sprite_params["layers"]*sprite_stack_factor-1))
                        global_l_surface.set_colorkey((0,0,0))
                        global_r_surface.set_colorkey((0,0,0))

                        for i in range(sprite_params["layers"]*sprite_stack_factor):
                            pos = (0,global_l_surface.get_height()-i-h)
                            l_surface = pg.Surface(base_layers[int(i/sprite_stack_factor)].get_size())
                            r_surface = pg.Surface(base_layers[int(i/sprite_stack_factor)].get_size())
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
                        train_sprites[key]["doors"][door_type][rotation] = {}
                        train_sprites[key]["doors"][door_type][rotation]["l"] = global_l_surface
                        train_sprites[key]["doors"][door_type][rotation]["r"] = global_r_surface

                    train_sprites[key]["doors"][door_type]["height"] = sprite_params["layers"]*sprite_stack_factor-1


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
                    sounds[key][sound].set_volume(0.0)
        progress+=1

    screen_state = "playing"
    consists = {}
    consist_key = random.randint(0,999)
    consists[consist_key] = Consist("type_a",train_types["type_a"],consists_info["type_a"],consist_key,world,[256*0.5,1024*6.125])

world = {
    (0,6):["tstr"],
    (0,5):["tsb1"],(-1,5):["tcb2"],
    (1,4):["stroitelnaya_platform_f","stroitelnaya_walls_f"],(0,4):["stroitelnaya_track_f_tstr"],(-1,4):["stroitelnaya_track_tstr"],(-2,4):["stroitelnaya_platform","stroitelnaya_walls"],
    (0,3):["tstr"],(-1,3):["tstr"],
    (1,2):["tca2"],(0,2):["tca1"],(-1,2):["tcb1"],(-2,2):["tcb2"],
    (1,1):["tstr"],(-2,1):["tstr"],
    (1,0):["park_kultury_track_tstr"],(0,0):["park_kultury_platform","park_kultury_walls"],(-1,0):["park_kultury_platform_f","park_kultury_walls_f"],(-2,0):["park_kultury_track_f_tstr"],
    (1,-1):["tstr"],(-2,-1):["tstr"],
    (1,-2):["tstr"],(-2,-2):["tstr"],
    (1,-3):["tstr"],(-2,-3):["tstr"],
    (1,-4):["kochetova_track_tstr"],(0,-4):["kochetova_platform","kochetova_walls"],(-1,-4):["kochetova_platform_f","kochetova_walls_f"],(-2,-4):["kochetova_track_f_tstr"],
    (1,-5):["tstr"],(-2,-5):["tstr"],
    (1,-6):["tstr"],(-2,-6):["tstr"],
    (1,-7):["tstr"],(-2,-7):["tstr"],
    (1,-8):["sodovaya_track_tstr"],(0,-8):["sodovaya_platform","sodovaya_walls"],(-1,-8):["sodovaya_platform_f","sodovaya_walls_f"],(-2,-8):["sodovaya_track_f_tstr"],
    (1,-9):["tcb1"],(0,-9):["tcb2"],(-1,-9):["tca2"],(-2,-9):["tca1"],
    (0,-10):["tstr"],(-1,-10):["tstr"],
    (0,-11):["tsa2"],(-1,-11):["tsa1"],
    (0,-12):["tstr"],(-1,-12):["tstr"]}

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
    (0,5):False,
    (0,-11):True,
    (-1,-11):True
}

#trains = {}

player_pos = [256*0.5,1024*0.5]
m_btn = [0,0,0]
world_mouse_coord = [0,0]
mouse_block_pos = (None,None)
mouse_clicked = False
mouse_released = False

sprite_thread = threading.Thread(target=sprite_load_routine,daemon=True) #,args=[world]
sprite_thread.start()

while working:
    tunnel_nothingness = (15,15,15)
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
    if screen_state == "loading":
        text_color = (200,200,200)
        screen.fill(tunnel_nothingness)
        text = font.render("загрузка...", True, text_color)
        screen.blit(text,(screen_size[0]/2-text.get_width()/2, screen_size[1]/2-text.get_height()))
        text = font.render(f"{round(progress/(len(sprite_loading_info)*5+len(train_folders))*100,1)}%", True, text_color)
        screen.blit(text,(screen_size[0]/2-text.get_width()/2, screen_size[1]/2+text.get_height()))


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
                    #pg.transform.scale(
                    ground_sprites[object[2]][world_angle]#,block_size)
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
                #sprite = train_sprites[train.type][(angle+train_params[3]*180)%360]
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
                    
        
        #for object in sorted(object_draw_queue,key= lambda z:-(abs(camera_pos[1]-z[1][1])**2+abs(camera_pos[0]-z[1][0])**2)): #олег помог с сортировкой #ОЛЕГКОГДАВИСТЕРИЯ
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
                r_train_sprite = train_sprites[object[2]]["doors"][object[5]["r" if object[6] else "l"]][object[3]]["r"]
                r_height = train_sprites[object[2]]["doors"][object[5]["r" if object[6] else "l"]]["height"]
                l_train_sprite = train_sprites[object[2]]["doors"][object[5]["l" if object[6] else "r"]][object[3]]["l"]
                l_height = train_sprites[object[2]]["doors"][object[5]["l" if object[6] else "r"]]["height"]
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
        mouse_block_pos = (int((player_pos[0]+world_mouse_coord[0]-(block_size[0] if player_pos[0]+world_mouse_coord[0] < 0 else 0))/block_size[0]),int((player_pos[1]+world_mouse_coord[1]-(block_size[1] if player_pos[1]+world_mouse_coord[1] < 0 else 0))/block_size[1]))
        if m_btn[0] and mouse_clicked:
            if mouse_block_pos in world and mouse_block_pos in switches:
                switches[mouse_block_pos] = not(switches[mouse_block_pos])

        #text =annotation_font.render(f"{world_mouse_coord}",True,(255,255,255))
        #screen.blit(text,(
        #    m_pos[0]+20,m_pos[1]+20
        #))
        #text =annotation_font.render(f"{dx,dy}",True,(255,255,255))
        #screen.blit(text,(
        #    m_pos[0]+20,m_pos[1]+40
        #))


        '''
        #
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
        ''' #здесь были маты, но на случай передачи кода их теперь тут нету
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
                                    #print(element["connection"],"left_doors",element["connection"] == "left_doors",trains[controlling].reversed,element["connection"] == "left_doors" and trains[controlling].reversed)
                                    if element["connection"] == "left_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["right_doors"] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    elif element["connection"] == "right_doors" and trains[controlling].reversed:
                                        consists[controlling_consist].control_wires["left_doors"] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    elif element["connection"] not in ["left_doors","right_doors"] or not trains[controlling].reversed:
                                        consists[controlling_consist].control_wires[element["connection"]] = consists[controlling_consist].consist_info["element_mapouts"][elem_id]["state"]
                                    if mouse_clicked and len(element["draw_mappings"][element["state"]]) == 7:
                                        sounds[consists[controlling_consist].train_type][element["draw_mappings"][element["state"]][6]].play()
                                elif element["type"] == "switch" and mouse_clicked and not mouse_clicked_prev:
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
                info_blit_list.append(font.render(f"CW doors {consists[controlling_consist].control_wires['left_doors'],consists[controlling_consist].control_wires['right_doors']}",True,text_color))
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