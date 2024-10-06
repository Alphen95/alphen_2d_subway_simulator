import math
import time
import threading
import random

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
                curblock = world[block_pos]
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
                        self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                elif curblock[-4:] == "tca2":
                    if local_pos[1] < 4*(39):
                        self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                    else:
                        self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
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
                    if int(self.angle) not in [0,180] or (local_pos[1] > 4*(256-2) and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] > 4*(256-39):
                            self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                        else:
                            self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                    else:
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsa2":
                    if self.angle not in [0,180] or (local_pos[1] < 4*(2) and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] < 4*(39):
                            self.angle = 180-8.25 if 270 >= self.angle >= 90 else 8.25
                        else:
                            self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                    else:
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsb1":
                    if int(self.angle) not in [0,180] or (local_pos[1] > 4*(256-2) and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] > 4*(256-39):
                            self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                        else:
                            self.angle = 180+16.5 if 270 >= self.angle >= 90 else 360-16.5
                    else:
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsb2":
                    if self.angle not in [0,180] or (local_pos[1] < 4*2 and block_pos in self.switches and self.switches[block_pos]):
                        if local_pos[1] < 4*(39):
                            self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                        else:
                            self.angle = 180+16.5  if 270 >= self.angle >= 90 else 360-16.5
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

        self.km = consist_info["default_km"]
        self.tk = consist_info["default_tk"]

        self.energy = 0
        self.engine_voltage = 0
        self.engine_current = 0
        self.electromotive_force = 0
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

        while self.exists:
            for elem_id, element in enumerate(self.consist_info["element_mapouts"]):
                if element["type"] == "lamp":
                    self.consist_info["element_mapouts"][elem_id]["state"] = self.control_wires[element["connection"]]
                elif element["type"] == "analog_scale":
                    value = 0
                    if element["scale"] == "velocity": value = self.velocity*3.6
                    elif element["scale"] == "amps": value = self.engine_current*self.traction_direction*self.control_wires["rp"]
                    elif element["scale"] == "volts": value = self.engine_voltage*self.control_wires["rp"]
                    elif element["scale"] == "press": value = (1 if self.pressure < 1 and self.control_wires["vz_1"] else self.pressure)

                    if value != element["angle"]:
                        self.consist_info["element_mapouts"][elem_id]["angle"] += (element["max_value"]-element["min_value"])/100*sign(value-element["angle"])
                        if self.consist_info["element_mapouts"][elem_id]["angle"] > element["max_value"]: self.consist_info["element_mapouts"][elem_id]["angle"] = element["max_value"]
                        elif self.consist_info["element_mapouts"][elem_id]["angle"] < element["min_value"]: self.consist_info["element_mapouts"][elem_id]["angle"] = element["min_value"]
                        elif abs(value-self.consist_info["element_mapouts"][elem_id]["angle"]) <(element["max_value"]-element["min_value"])/100: self.consist_info["element_mapouts"][elem_id]["angle"] = value


            if self.consist_info["control_system_type"] == "direct":
                if self.control_wires["rp_return"] and self.km == 0:
                    self.control_wires["rp"] = True

                self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi*self.transmissional_number
                engine_power = 0
                if self.consist_info["km_mapouts"][str(self.km)]["type"] == "accel" and self.controlling_direction != 0 and self.control_wires["rp"]:
                    self.engine_voltage = self.consist_info["km_mapouts"][str(self.km)]["voltage"]
                    self.traction_direction = self.controlling_direction*sign(self.engine_voltage)
                    if self.velocity_direction == 0: 
                        self.velocity_direction = self.traction_direction
                    self.engine_current = (abs(self.engine_voltage)-(self.electromotive_force*(1 if self.traction_direction == self.velocity_direction else -1)))/self.engine_resistance
                    if self.engine_current >= self.consist_info["peril_current"]:
                        self.control_wires["rp"] = False
                        self.engine_current = 0
                        self.engine_voltage = 0
                    engine_power = abs(self.engine_voltage)*self.engine_current*(self.velocity_direction*self.traction_direction) if self.engine_current > 0 and self.control_wires["rp"] else 0
                
                if self.consist_info["tk_mapouts"][str(self.tk)]["type"] == "press":
                    if self.pressure != self.consist_info["tk_mapouts"][str(self.tk)]["target"]:
                        if abs(self.pressure - self.consist_info["tk_mapouts"][str(self.tk)]["target"]) < self.consist_info["tk_mapouts"][str(self.tk)]["speed"]:
                            self.pressure = self.consist_info["tk_mapouts"][str(self.tk)]["target"]
                        else:
                            self.pressure+=-sign(self.pressure - self.consist_info["tk_mapouts"][str(self.tk)]["target"])*self.consist_info["tk_mapouts"][str(self.tk)]["speed"]

                self.control_wires["traction"] = engine_power > 0
                self.control_wires["maximal_traction"] = self.km == self.consist_info["max_km"]
                self.control_wires["reversor_forwards"] = self.controlling_direction == 1
                self.control_wires["reversor_backwards"] = self.controlling_direction == -11

                engine_power*=engines

                kinetic_energy = self.mass*self.velocity**2/2*self.train_amount
                revolutional_energy = self.wheel_mass*self.wheel_radius**2*self.angular_velocity**2/4*wheels
                friction_energy = 0.004*self.wheel_mass*9.81*self.angular_velocity
                break_friction_energy = wheels*1*self.velocity*((1 if self.pressure < 1 and self.control_wires["vz_1"] else self.pressure)*100000*self.break_cyllinder_surface)

                self.energy = round(kinetic_energy+revolutional_energy+engine_power*self.transmissional_number/120-friction_energy/120-break_friction_energy/120,5)
                self.velocity = ((2*self.energy*self.wheel_radius**2)/(self.train_amount*self.mass*self.wheel_radius**2+wheels*self.wheel_mass*self.wheel_radius**2/2))**0.5
                self.velocity = round(complex(self.velocity).real,5)
                self.angular_velocity = round(self.velocity*self.wheel_radius,5)
                if self.velocity == 0: self.velocity_direction = 0


            speed_modifier = 1
            #self.humainzed_velocity = round(self.velocity*120*0.15/4*speed_modifier,5)
            self.pixel_velocity = round(self.velocity/120/0.15*4*speed_modifier,5)

            for train_id in self.linked_to:
                trains[train_id].velocity = self.velocity
                trains[train_id].pos[0]+=round(math.sin(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)
                trains[train_id].pos[1]+=round(math.cos(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)

            time.sleep(1/120)