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
                    #if local_pos[1] > 4*(256-39):
                    #    self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                    #else:
                    #    self.angle = 180-16.5 if 270 >= self.angle >= 90 else 16.5
                    self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                elif curblock[-4:] == "tca2":
                    #if local_pos[1] < 4*(39):
                    #    self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                    #else:
                    #    self.angle = 180-16.5 if 270 >= self.angle >= 90 else 16.5
                    self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                elif curblock[-4:] == "tcb1":
                    #if local_pos[1] > 4*(256-39):
                    #    self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                    #else:
                    #    self.angle = 180+16.5 if 270 >= self.angle >= 90 else 360-16.5
                    self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
                elif curblock[-4:] == "tcb2":
                    #if local_pos[1] < 4*(39):
                    #    self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                    #else:
                    #    self.angle = 180+16.5  if 270 >= self.angle >= 90 else 360-16.5
                    self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
                
                elif curblock[-4:] == "tsa1":
                    if int(self.angle) not in [0,180] or ((local_pos[1] > 4*(256-2) or local_pos[1] < 4*64) and block_pos in self.switches and self.switches[block_pos]):
                        #if local_pos[1] > 4*(256-39):
                        #    self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                        #elif local_pos[1] > 4*64:
                        #    self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                        if local_pos[1] > 4*64:
                            self.angle = 180-14 if 270 >= self.angle >= 90 else 14
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
                        #if local_pos[1] < 4*(39):
                        #    self.angle = 180-8.25 if 270 >= self.angle >= 90 else 8.25
                        #elif local_pos[1] < 4*(64*3):
                        #    self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                        if local_pos[1] < 4*64*3:
                            self.angle = 180-14 if 270 >= self.angle >= 90 else 14
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
                        #if local_pos[1] > 4*(256-39):
                        #    self.angle = 180-8.25 if 270 >= self.angle >= 90 else 0+8.25
                        #elif local_pos[1] > 4*64:
                        #    self.angle = 163.5 if 270 >= self.angle >= 90 else 16.5
                        if local_pos[1] > 4*64:
                            self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
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
                        #if local_pos[1] < 4*(39):
                        #    self.angle = 180+8.25 if 270 >= self.angle >= 90 else 360-8.25
                        #elif local_pos[1] < 4*(64*3):
                        #    self.angle = 180+16.5  if 270 >= self.angle >= 90 else 360-16.5

                        if local_pos[1] < 4*(64*3):
                            self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
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
    def __init__(self,train_type,train_sprite,params,consist_info,self_id,world,spawn_pos):
        global trains

        self.linked_to = []
        self.pressure = 0
        self.tank_pressure = 0
        self.vz_pressure = 0
        self.velocity = 0
        self.pixel_velocity = 0
        self.angular_velocity = 0
        self.train_type = train_type
        self.train_sprite = train_sprite
        self.wheel_radius = consist_info["wheel_radius"]
        self.mass = consist_info["mass"]
        self.wheel_mass = consist_info["wheel_mass"]
        self.humainzed_velocity = 0
        self.current_roll_sound = -1

        self.control_wires ={
            "main_power":False, #Главный разъединитель и главный автомат
            "reserve_controls":False, #Резервное управление
            "batteries":False, #2 Питание батарей
            "mk":False, #3 Питание мотор-компрессора
            "reserve_mk":False, #4 Питание резервного мотор-компрессора
            "reversor_forwards":False, #5 Реверс вперёд
            "reversor_backwards":False, #6 Реверс назад
            "rp":True, #7 Реле перегрузки (False = требует восстановки)
            "rp_return":False, #8 Возврат реле перегрузки
            "vz_1":False, #9 Вентиль замещения №1
            "vz_2":False, #10 Вентиль замещения №2
            "vz_1_km":False, # Вентиль замещения №1 от ходового режима
            "vz_2_km":False, # Вентиль замещения №2 от ходового режима
            "traction":False, #11 Сбор схемы на ход
            "electro_brake":False, #12 Сбор схемы на торможение
            "maximal_traction":False, #13 Сбор схемы на максимальный ход
            "rk_fail":False, #33 Несбор схемы (N=0 при U!=0)
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
            "slow_accel":False, #33 Понижение ускорения (Регулировка РУТ)
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
        self.rk = 0
        self.rk_timer = 0
        self.timer = 0

        self.energy = 0
        self.engine_power = 0
        self.engine_voltage = 0
        self.engine_current = 0
        self.ballast_resistance = 0
        self.electromotive_force = 0
        self.vz_1 = 0
        self.vz_2 = 0
        self.engine_constant = consist_info["engine_constant"]
        self.engine_resistance = consist_info["engine_resistance"]
        self.transmissional_number = consist_info["transmissional_number"]
        self.brake_cyllinder_surface = consist_info["brake_cyllinder_surface"]

        self.pressure_tank_volume = consist_info["pressure_tank_volume"]
        self.brake_cyllinder_volume = consist_info["brake_cyllinder_volume"]
        self.compressor_mass_rate = consist_info["compressor_mass_rate"]
        self.peril_pressure = consist_info["peril_pressure"]
        self.target_pressure = consist_info["target_pressure"]
        self.compressor_active = False

        self.controlling_direction = 0
        self.traction_direction = 0
        self.velocity_direction = 0

        pos = spawn_pos
        self.train_amount = 3
        for i in range(self.train_amount):
            train_id = random.randint(0,99999)
            trains[train_id] = Train([pos[0],pos[1]+320*i],train_sprite, i+1==self.train_amount,params["size"],self_id,world)
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
            # необходимые просчёты физики, пневматики, электрики, проводов   
            self.cycle_electro()
            self.cycle_pneumo()   
            self.cycle_physics()
            self.cycle_control_wires()
            self.update_railcars()

            # декоративно-графическое
            self.update_door_states()
            self.update_graphics_states()

            if self.rk_timer > 0: self.rk_timer -= 1
            self.timer=(self.timer+1)%120
            time.sleep(1/120)

    def cycle_electro(self):
        # блок логики обсчёта электротяговых систем - НСУ, РКСУ, РКСУ+, ТИСУ и т. д.
        pi = 3.1415
        self.engine_power = 0
        
        
        #вентиль замещения 1
        if "vz_1" in self.consist_info["km_mapouts"][str(self.km)] and self.consist_info["km_mapouts"][str(self.km)]["vz_1"]:
            if "vz_1_pos" in self.consist_info["km_mapouts"][str(self.km)] and self.rk in self.consist_info["km_mapouts"][str(self.km)]["vz_1_pos"] or "vz_1_pos" not in self.consist_info["km_mapouts"][str(self.km)]:
                self.control_wires["vz_1_km"] = True
            else: self.control_wires["vz_1_km"] = False
        else: self.control_wires["vz_1_km"] = False

        #вентиль замещения 2
        if "vz_2" in self.consist_info["km_mapouts"][str(self.km)] and self.consist_info["km_mapouts"][str(self.km)]["vz_2"]:
            if "vz_2_pos" in self.consist_info["km_mapouts"][str(self.km)] and self.rk in self.consist_info["km_mapouts"][str(self.km)]["vz_2_pos"] or "vz_2_pos" not in self.consist_info["km_mapouts"][str(self.km)]:
                self.control_wires["vz_2_km"] = True
            else: self.control_wires["vz_2_km"] = False
        else: self.control_wires["vz_2_km"] = False

        if self.consist_info["control_system_type"] == "direct":
            self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi*self.transmissional_number*(self.consist_info["km_mapouts"][str(self.km)]["coil_engagement"]/100 if "coil_engagement" in self.consist_info["km_mapouts"][str(self.km)] else 1)
            # логика обсчёта НСУ (непосредственной системы управления)
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
                self.engine_power = abs(self.engine_voltage)*self.engine_current*(self.velocity_direction*self.traction_direction) if self.engine_current > 0 and self.control_wires["rp"] else 0

        elif self.consist_info["control_system_type"] == "reostat":
            #логика обсчёта РКСУ
            self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi*self.transmissional_number*(self.consist_info["rk_mapouts"][str(self.rk)]["coil_engagement"]/100 if "coil_engagement" in self.consist_info["rk_mapouts"][str(self.rk)] else 1)
            if self.consist_info["km_mapouts"][str(self.km)]["type"] == "accel":

                #режим разгона

                if self.controlling_direction != 0 and self.control_wires["rp"]:
                    if str(self.rk) != "0":
                        self.engine_voltage = self.consist_info["rk_mapouts"][str(self.rk)]["voltage"]
                    
                    if (self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][-1] > self.rk and 
                        self.consist_info["rk_mapouts"][str(self.rk)]["switch_current"] > self.engine_current and self.rk_timer <= 0):
                        if self.rk not in self.consist_info["km_mapouts"][str(self.km)]["rk_positions"]:
                            self.rk = self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][0]
                        elif self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][-1] > self.rk:
                            self.rk = self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][self.consist_info["km_mapouts"][str(self.km)]["rk_positions"].index(self.rk)+1]
                        self.rk_timer = self.consist_info["km_mapouts"][str(self.km)]["switch_time"]
                        self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi*self.transmissional_number*(self.consist_info["rk_mapouts"][str(self.rk)]["coil_engagement"]/100 if "coil_engagement" in self.consist_info["rk_mapouts"][str(self.rk)] else 1)
                        self.engine_current = (abs(self.engine_voltage)-(self.electromotive_force*(1 if self.traction_direction == self.velocity_direction else -1)))/self.engine_resistance
                        if self.engine_current <= 0: self.rk_timer = 12
                else:
                    self.rk_timer = 0
                    self.engine_voltage = 0
                self.traction_direction = self.controlling_direction*sign(self.engine_voltage)
                if self.velocity_direction == 0: 
                    self.velocity_direction = self.traction_direction
                self.engine_current = (abs(self.engine_voltage)-(self.electromotive_force*(1 if self.traction_direction == self.velocity_direction else -1)))/self.engine_resistance
                if self.engine_current <= 0: self.engine_current = 0
                if self.engine_current >= self.consist_info["peril_current"]:
                    self.control_wires["rp"] = False
                    self.engine_current = 0
                    self.engine_voltage = 0
                self.engine_power = abs(self.engine_voltage)*self.engine_current*(self.velocity_direction*self.traction_direction) if self.engine_current > 0 and self.control_wires["rp"] else 0
            elif self.consist_info["km_mapouts"][str(self.km)]["type"] == "brake":
                #режим торможения

                #электродинамическое торможение
                if self.controlling_direction != 0 and self.control_wires["rp"]:
                    if str(self.rk) != "0":
                        self.ballast_resistance = self.consist_info["rk_mapouts"][str(self.rk)]["resistance"]

                    if (self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][-1] < self.rk and 
                        (
                            (self.consist_info["rk_mapouts"][str(self.rk)]["switch_current"] > self.engine_current 
                             and self.rk_timer <= 0) or
                             self.rk not in self.consist_info["km_mapouts"][str(self.km)]["rk_positions"]
                        )): #переключиться, если вышел таймер и нужное напряжение и не макспозиция ИЛИ позиция не в словаре
                        if self.rk not in self.consist_info["km_mapouts"][str(self.km)]["rk_positions"]:
                            self.rk = self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][0] #первая, если старой нету
                        elif self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][-1] < self.rk:
                            rk_index = self.consist_info["km_mapouts"][str(self.km)]["rk_positions"].index(self.rk)+1
                            self.rk = self.consist_info["km_mapouts"][str(self.km)]["rk_positions"][rk_index] #переход на следующую, если есть
                        self.rk_timer = self.consist_info["km_mapouts"][str(self.km)]["switch_time"] #восстановка таймера
                    self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi*self.transmissional_number*(self.consist_info["rk_mapouts"][str(self.rk)]["coil_engagement"]/100 if "coil_engagement" in self.consist_info["rk_mapouts"][str(self.rk)] else 1)
                    self.engine_current = ((self.electromotive_force*(1 if self.traction_direction == self.velocity_direction else -1)))/(self.engine_resistance+self.ballast_resistance)
                    if self.engine_current <= 0: self.rk_timer = 12 #если нету напряжения, то урезать таймер
                else:
                    self.rk_timer = 0
                    self.engine_voltage = 0

                if self.engine_current > 0 and self.control_wires["rp"] and self.ballast_resistance != 0:
                    self.engine_power = -self.electromotive_force**2*(self.velocity_direction*self.traction_direction)/self.ballast_resistance
                else: self.engine_power = 0

            else:
                self.rk = 0
                self.engine_current = 0
                self.engine_voltage = 0
                self.ballast_resistance = 0

    def cycle_pneumo(self):
        # блок логики обсчёта пневматических систем - МК, РМК, ТЦ, ВЗ№1 и ВЗ№2

        # обсчёт мотор-компрессора
        if self.compressor_active: 
            self.tank_pressure+=self.compressor_mass_rate*8.31*293/self.pressure_tank_volume/0.029/120/10000

        # обсчёт вентиля замещения №1
        self.vz_1 = (self.vz_1 + (2*(self.control_wires["vz_1"] or self.control_wires["vz_1_km"])-1)*self.consist_info["valve_params"]["vz_1"][1]) 
        self.vz_1 = (self.vz_1 if self.vz_1 >= 0 else 0)
        self.vz_1 = (self.vz_1 if self.vz_1 <= self.consist_info["valve_params"]["vz_1"][0] else self.consist_info["valve_params"]["vz_1"][0])

        # обсчёт вентиля замещения №2
        self.vz_2 = (self.vz_2 + (2*(self.control_wires["vz_2"] or self.control_wires["vz_2_km"])-1)*self.consist_info["valve_params"]["vz_2"][1]) 
        self.vz_2 = (self.vz_2 if self.vz_2 >= 0 else 0)
        self.vz_2 = (self.vz_2 if self.vz_2 <= self.consist_info["valve_params"]["vz_2"][0] else self.consist_info["valve_params"]["vz_2"][0])

        # обсчёт тормозных цилиндров
        if self.consist_info["tk_mapouts"][str(self.tk)]["type"] == "press":
            if self.pressure != self.consist_info["tk_mapouts"][str(self.tk)]["target"]:
                if abs(self.pressure - self.consist_info["tk_mapouts"][str(self.tk)]["target"]) < self.consist_info["tk_mapouts"][str(self.tk)]["speed"]:
                    self.pressure = self.consist_info["tk_mapouts"][str(self.tk)]["target"]
                else:
                    if (-sign(self.pressure - self.consist_info["tk_mapouts"][str(self.tk)]["target"]) > 0 and 
                        self.tank_pressure > self.consist_info["tk_mapouts"][str(self.tk)]["speed"]*self.brake_cyllinder_volume/self.pressure_tank_volume and
                        self.tank_pressure >= self.pressure):
                        self.tank_pressure-=self.consist_info["tk_mapouts"][str(self.tk)]["speed"]*self.brake_cyllinder_volume/self.pressure_tank_volume
                        self.pressure+=self.consist_info["tk_mapouts"][str(self.tk)]["speed"]
                    elif -sign(self.pressure - self.consist_info["tk_mapouts"][str(self.tk)]["target"]) < 0:
                        self.pressure-=self.consist_info["tk_mapouts"][str(self.tk)]["speed"]

    def cycle_physics(self):
        # блок логики физических просчётов (т. е. обновление скорости вагона)
        wheels = 8*self.train_amount
        engines = 2*self.train_amount

        self.engine_power*=engines
        kinetic_energy = self.mass*(self.velocity**2)/2*self.train_amount
        revolutional_energy = self.wheel_mass*self.wheel_radius**2*self.angular_velocity**2/4*wheels
        friction_energy = 0.05*self.wheel_mass*9.81*self.angular_velocity
        brake_friction_energy = wheels*1*self.velocity*(max(self.pressure,self.vz_1,self.vz_2)*100000*self.brake_cyllinder_surface)

        self.energy = round(kinetic_energy+revolutional_energy+self.engine_power*self.transmissional_number/120-friction_energy/120-brake_friction_energy/120,5)
        self.velocity = ((2*self.energy*self.wheel_radius**2)/(self.train_amount*self.mass*self.wheel_radius**2+wheels*self.wheel_mass*self.wheel_radius**2/2))**0.5
        self.velocity = round(complex(self.velocity).real,5)
        self.angular_velocity = round(self.velocity/self.wheel_radius,5)
        if self.velocity == 0: self.velocity_direction = 0  


    def cycle_control_wires(self):
        # блок логики обновления проводов управления-состояния
        self.control_wires["traction"] = self.engine_power > 0
        self.control_wires["rk_fail"] = self.engine_power == 0 and self.consist_info["km_mapouts"][str(self.km)]["type"] == "accel"
        self.control_wires["maximal_traction"] = self.km == self.consist_info["max_km"]
        self.control_wires["reversor_forwards"] = self.controlling_direction == 1
        self.control_wires["reversor_backwards"] = self.controlling_direction == -1

        
        if self.control_wires["mk"] and (self.tank_pressure <= self.peril_pressure or self.tank_pressure < self.target_pressure and self.compressor_active):
            self.compressor_active = True
        else: self.compressor_active = False

        if self.control_wires["rp_return"] and self.km == 0:
            self.control_wires["rp"] = True
        
        if self.control_wires["right_doors"] and self.doors["r"] == "closed":
                self.doors["action_r"] = "open"
        if self.control_wires["left_doors"] and self.doors["l"] == "closed":
            self.doors["action_l"] = "open"
        if self.control_wires["close_doors"] or self.control_wires["reserve_close_doors"]:
            self.doors["action_r"] = "close" if self.doors["r"] != "closed" else None
            self.doors["action_l"] = "close" if self.doors["l"] != "closed" else None
        self.control_wires["doors_open"] = self.doors["r"] != "closed" or self.doors["l"] != "closed"


    def update_door_states(self):
        # блок логики открытия-закрытия дверей
        z = list(self.consist_info["door_animation_states"].keys())
        if self.doors["action_r"] == "open":
            if self.doors["timer_r"] == 0:
                self.doors["r"] = z[z.index(self.doors["r"])+1]
                if self.doors["r"] != "open":
                    self.doors["timer_r"] = self.consist_info["door_animation_states"][self.doors["r"]]
                else:
                    self.doors["action_r"] = None
            if self.doors["timer_r"] > 0: self.doors["timer_r"] -= 1
        elif self.doors["action_r"] == "close":
            if self.doors["timer_r"] == 0:
                self.doors["r"] = z[z.index(self.doors["r"])-1]
                if self.doors["r"] != "closed":
                    self.doors["timer_r"] = self.consist_info["door_animation_states"][self.doors["r"]]
                else:
                    self.doors["action_r"] = None
            if self.doors["timer_r"] > 0: self.doors["timer_r"] -= 1

        if self.doors["action_l"] == "open":
            if self.doors["timer_l"] == 0:
                self.doors["l"] = z[z.index(self.doors["l"])+1]
                if self.doors["l"] != "open":
                    self.doors["timer_l"] = self.consist_info["door_animation_states"][self.doors["l"]]
                else:
                    self.doors["action_l"] = None
            if self.doors["timer_l"] > 0: self.doors["timer_l"] -= 1
        elif self.doors["action_l"] == "close":
            if self.doors["timer_l"] == 0:
                self.doors["l"] = z[z.index(self.doors["l"])-1]
                if self.doors["l"] != "closed":
                    self.doors["timer_l"] = self.consist_info["door_animation_states"][self.doors["l"]]
                else:
                    self.doors["action_l"] = None
            if self.doors["timer_l"] > 0: self.doors["timer_l"] -= 1


    def update_graphics_states(self):
        # блок логики обновления лампочек и x-метров
        for elem_id, element in enumerate(self.consist_info["element_mapouts"]):
            if element["type"] == "lamp":
                self.consist_info["element_mapouts"][elem_id]["state"] = self.control_wires[element["connection"]]
            elif element["type"] == "analog_scale":
                value = 0
                if element["scale"] == "velocity": value = round(complex(self.velocity*3.6).real,2)
                elif element["scale"] == "amps": value = round(
                    self.engine_current*self.traction_direction*self.velocity_direction*self.control_wires["rp"],2)
                elif element["scale"] == "volts": value = round(self.engine_voltage*self.control_wires["rp"],2)
                elif element["scale"] == "press": value = round(max(self.vz_1,self.vz_2,self.pressure),2)
                elif element["scale"] == "press_tank": value = round(self.tank_pressure,2)

                if value != element["angle"]:
                    self.consist_info["element_mapouts"][elem_id]["angle"] += (element["max_value"]-element["min_value"])/100*sign(value-element["angle"])
                    if self.consist_info["element_mapouts"][elem_id]["angle"] > element["max_value"]: self.consist_info["element_mapouts"][elem_id]["angle"] = element["max_value"]
                    elif self.consist_info["element_mapouts"][elem_id]["angle"] < element["min_value"]: self.consist_info["element_mapouts"][elem_id]["angle"] = element["min_value"]
                    elif abs(value-self.consist_info["element_mapouts"][elem_id]["angle"]) <(element["max_value"]-element["min_value"])/100: self.consist_info["element_mapouts"][elem_id]["angle"] = value


    def update_railcars(self):
        # блок логики движения вагонов
        speed_modifier = 1
        #self.humainzed_velocity = round(self.velocity*120*0.15/4*speed_modifier,5)
        self.pixel_velocity = round(self.velocity/120/0.15*4*speed_modifier,5)

        for train_id in self.linked_to:
            trains[train_id].velocity = self.velocity
            trains[train_id].pos[0]+=round(math.sin(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)
            trains[train_id].pos[1]+=round(math.cos(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)