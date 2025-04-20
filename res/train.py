import math
import time
import threading
import random
import copy

trains = {}
signal_states = {}

def sign(x):
    if x > 0: return 1
    elif x < 0: return -1
    else: return 0

class SignalSystem():
    def __init__(self,signals):
        global signal_states
        self.train_grid = []
        self.signals = signals

        for signal_id in self.signals:
            signal_states[signal_id] = {"occupied":False,"aspect":"green","max_speed":0}

        self.is_working = True
        self.thread = threading.Thread(target=self.cycle,daemon=True)
        self.thread.start()

    def cycle(self):
        global trains, signal_states
        block_size = (256,1024)

        aspects_ab_full = {
            "red":"red_protector",
            "red_protector":"red_yellow",
            "red_yellow":"yellow",
            "yellow":"yellow_green",
            "yellow_green":"green",
            "green":"green"
        }
        
        aspects_ab_velocity = {
            "red":0,
            "red_protector":1,
            "red_yellow":2,
            "yellow":3,
            "yellow_green":4,
            "green":5
        }

        print("Signal thread started.")

        while self.is_working:
            self.train_grid = []

            for train_id in trains:
                train_block_pos = (
                    trains[train_id].pos[0]//block_size[0],
                    trains[train_id].pos[1]//block_size[1],
                )
                self.train_grid.append(train_block_pos)

            for signal_id in self.signals:
                checked_tiles = self.signals[signal_id]["tiles"]
                block_occupied = False
                for tile in checked_tiles:
                    if tile in self.train_grid:
                        signal_states[signal_id]["occupied"] = True
                        #signal_states[signal_id]["aspect"] = "red"
                        block_occupied = True
                        break
                if not block_occupied: 
                    signal_states[signal_id]["occupied"] = False

                if "next" in self.signals[signal_id] and self.signals[signal_id]["next"] not in [None,"",'']:
                    next_id = self.signals[signal_id]["next"]
                    if not signal_states[next_id]["occupied"] or signal_states[next_id]["aspect"] == "red":
                        next_aspect = signal_states[next_id]["aspect"]
                        signal_states[signal_id]["aspect"] = aspects_ab_full[next_aspect]
                    else:
                        signal_states[signal_id]["aspect"] = "red"
                elif "next" not in self.signals[signal_id] or "next" in self.signals[signal_id] and self.signals[signal_id]["next"] in [None,"",'']:
                    signal_states[signal_id]["aspect"] = "green"
                
                if self.signals[signal_id]["speed"] != "":
                    velocity_states = self.signals[signal_id]["speed"].split("-")
                    signal_states[signal_id]["max_speed"] = int(velocity_states[min(aspects_ab_velocity[signal_states[signal_id]["aspect"]],len(velocity_states)-1)])
                else:
                    signal_states[signal_id]["max_speed"] = 20
            
            time.sleep(1/30) #просчёт 30 раз в секунду

        print("Signal thread stopped.")

class Train():
    def __init__(self,pos,type, reversed,size,consist,world,autodrive_map,reversed_signals):
        self.pos = pos
        self.local_pos = (0,0)
        self.type = type
        self.velocity = 0
        self.signed_velocity = 0
        self.angle = 180
        self.reversed = reversed
        self.size = size
        self.consist = consist
        self.signal_state = None
        self.signal_velocity_state = 0
        self.switches = {}
        self.autodrive_marker = ""
        self.autodrive_map = autodrive_map

        self.exists = True
        self.thread = threading.Thread(target=self.cycle,args=[world,reversed_signals],daemon=True)
        self.thread.start()
        self.switches = []

    def cycle(self,world,reversed_signals):
        global signal_states
        block_size = (256,1024)


        while self.exists:
            block_pos = (int((self.pos[0]-(block_size[0] if self.pos[0] < 0 else 0))/block_size[0]),int((self.pos[1]-(block_size[1] if self.pos[1] < 0 else 0))/block_size[1]))
            local_pos = (self.pos[0]%block_size[0],self.pos[1]%block_size[1])
            self.local_pos = local_pos

            if block_pos in world:
                if block_pos in reversed_signals and "next" in reversed_signals[block_pos] and reversed_signals[block_pos]["next"] not in [None,"",'']:
                    self.signal_state = signal_states[reversed_signals[block_pos]["next"]]
                else:
                    self.signal_state = None

                if block_pos in reversed_signals:
                    self.signal_velocity_state = signal_states[reversed_signals[block_pos]["cur"]]["max_speed"]
                else:
                    self.signal_velocity_state = 20

                if block_pos in self.autodrive_map:
                    self.autodrive_marker = self.autodrive_map[block_pos]
                else:
                    self.autodrive_marker = ""

                curblock = world[block_pos][0] if type(world[block_pos]) == list else world[block_pos]

                velocity_vector_direction = (2*(90 <= self.angle <= 270)-1)*sign(self.signed_velocity)

                vvd_read = {1:"up",0:"neutral",-1:"down"}

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

                elif curblock[-4:] == "tcx2":
                    if local_pos[1] < 4*64:
                        self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                    elif local_pos[1] > 4*192:
                        self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14

                elif curblock[-4:] == "tcx1":
                    if local_pos[1] < 4*64:
                        self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
                    elif local_pos[1] > 4*192:
                        self.angle = 180-14 if 270 >= self.angle >= 90 else 14

                elif curblock[-4:] == "tsa1":
                    if (4*192 < local_pos[1] < 4*254 and velocity_vector_direction == 1 and
                        block_pos in self.switches and self.switches[block_pos]):
                        self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                    
                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsa2":
                    if (4*2 < local_pos[1] < 4*64  and velocity_vector_direction == -1 and
                        block_pos in self.switches and self.switches[block_pos]):
                        self.angle = 180-14 if 270 >= self.angle >= 90 else 14

                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                elif curblock[-4:] == "tsb1":
                    if (4*192 < local_pos[1] < 4*254 and velocity_vector_direction == 1 and
                        block_pos in self.switches and self.switches[block_pos]):
                        self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
                        
                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]

                elif curblock[-4:] == "tsb2":
                    if (4*2 < local_pos[1] < 4*64 and velocity_vector_direction == -1 and
                        block_pos in self.switches and self.switches[block_pos]):
                        self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
                        
                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                
                elif curblock[-4:] == "tsx1":
                    if block_pos in self.switches and self.switches[block_pos]:
                        if 4*192 < local_pos[1] < 4*254 and velocity_vector_direction == 1:
                            self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                        if 4*2 < local_pos[1] < 4*64 and velocity_vector_direction == -1:
                            self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
                        
                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
                    
                elif curblock[-4:] == "tsx2":
                    if block_pos in self.switches and self.switches[block_pos]:
                        if 4*2 < local_pos[1] < 4*64  and velocity_vector_direction == -1:
                            self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                        if 4*192 < local_pos[1] < 4*254 and velocity_vector_direction == 1:
                            self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14
                        
                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]

                elif curblock[-4:] == "tsy1":
                    if (4*192 < local_pos[1] < 4*254 and velocity_vector_direction == 1 and
                        block_pos in self.switches):
                        if self.switches[block_pos]:
                            self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                        else:
                            self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14

                    
                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]

                elif curblock[-4:] == "tsy2":
                    if (4*2 < local_pos[1] < 4*64  and velocity_vector_direction == -1 and
                        block_pos in self.switches):
                        if self.switches[block_pos]:
                            self.angle = 180-14 if 270 >= self.angle >= 90 else 14
                        else:
                            self.angle = 180+14 if 270 >= self.angle >= 90 else 360-14

                    
                    if not(2*4 <= local_pos[1] <= 254*4):
                        self.angle = 180 if 270 >= self.angle >= 90 else 0
                        if local_pos[0] < 127.95:
                            self.pos[0] += 0.05
                        elif local_pos[0] > 128.05:
                            self.pos[0] -= 0.05
                        
                        if 127.95 <= local_pos[0] <= 128.05 and local_pos[0] != 128:
                            self.pos[0] += 128-local_pos[0]
            
            
            time.sleep(1/120)

class Consist():
    def __init__(self,train_type,train_sprite,params,consist_info,self_id,world,autodrive_map,reversed_signals,spawn_pos):
        global trains

        self.linked_to = []
        self.first_car = -1
        self.last_car = -1

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
            "batteries":False, # Питание батарей
            "mk":False, # Питание мотор-компрессора
            "reserve_mk":False, # Питание резервного мотор-компрессора
            "reversor_forwards":False, # Реверс вперёд
            "reversor_backwards":False, # Реверс назад
            "rp":True, # Реле перегрузки (False = требует восстановки)
            "rp_return":False, # Возврат реле перегрузки
            "vz_1":False, # Вентиль замещения №1
            "vz_2":False, # Вентиль замещения №2
            "vz_ad":False, # Вентиль автоведения
            "vz_1_km":False, # Вентиль замещения №1 от ходового режима
            "vz_2_km":False, # Вентиль замещения №2 от ходового режима
            "traction":False, # Сбор схемы на ход
            "electro_brake":False, # Сбор схемы на торможение
            "maximal_traction":False, # Сбор схемы на максимальный ход
            "rk_fail":False, # Несбор схемы (N=0 при U!=0)
            "rk_spin":False, # Вращение реостатного контроллера
            "rk_spin_direction":0, # Направление поворота реостатного контроллера (-1 - в минус, 0 - не трогать, 1 - в плюс)
            "rk_maxed":False, # Схема собрана (РК на максимальной допустимой позиции)
            "left_doors":False, # Открытие левых дверей
            "right_doors":False, # Открытие правых дверей
            "close_doors":False, # Закрытие дверей
            "reserve_close_doors":False, # Резервное закрытие дверей
            "doors_open":False, # Двери открыты
            "doors_open_duplicate":False, # Двери открыты
            "light_on":False, # Включение освещения
            "light_off":False, # Выключение освещения
            "slow_accel":False, # Понижение ускорения (Регулировка реле управления током)
            "ars":False, # Включение АРС
            "ars_fuse":False, # Предохранитель АРС (False - запрет на движение, требует восстановки)
            "als":False, # Включение АЛС
            "ars_0":False, # АРС - 0 км/ч
            "ars_20":False, # АРС - ОЧ [20 км/ч]
            "ars_40":False, # АРС - 40 км/ч
            "ars_60":False, # АРС - 60 км/ч
            "ars_70":False, # АРС - 70 км/ч
            "ars_80":False, # АРС - 80 км/ч
            "ars_braking_safety":False, # АРС - Кнопка восприятия торможения
            "ars_braking_safety_auto":False, # АРС - Кнопка восприятия торможения от АВ
            "ars_traction_disable":False, # АРС - Отключение ходового режима
            "ars_speed_equality":False, # АРС - Равенство скоростей
            "ars_direction":False, # АРС - Соответствие направления
            "braking_control":False, # Контроль торможения - давление в ТЦ > 0
            "autodrive":False, # Включение автоведения
            "autodrive_door_delay":False, # Задержка дверей от автоведения
            "autodrive_train_delay":False, # Задержка поезда от автоведения
            "ring":False, # Звонок
            "unused":False, # Специальный нейтральный провод для "пустых" выключателей и ламп

        }
        self.consist_info = copy.deepcopy(consist_info)
        self.doors = {
            "l":"closed",
            "r":"closed",
            "timer_l":0,
            "timer_r":0,
            "action_l":None,
            "action_r":None,
            "sound_l":"",
            "sound_r":"",
        }

        self.km = consist_info["default_km"]
        self.tk = consist_info["default_tk"]
        self.rk = 0
        self.rk_timer = 0
        self.timer = 0
        self.ars_speed = 0

        self.energy = 0
        self.engine_power = 0
        self.engine_voltage = 0
        self.engine_current = 0
        self.ballast_resistance = 0
        self.electromotive_force = 0
        self.vz_1 = 0
        self.vz_2 = 0
        self.vz_ad = 0
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

        self.control_wires["ars_fuse"] = not(self.consist_info["has_ars"])
        self.autodrive_state = {"timer": 0, "state":None}

        pos = spawn_pos
        self.train_amount = 3
        for i in range(self.train_amount):
            while True:
                train_id = random.randint(0,99999)
                if train_id not in trains: break
            trains[train_id] = Train([pos[0],pos[1]+320*i],train_sprite, i+1==self.train_amount,params["size"],self_id,world,autodrive_map,reversed_signals)
            self.linked_to.append(train_id)
        self.first_car, self.last_car = self.linked_to[0], self.linked_to[-1]

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
            self.cycle_electro() # электрооборудование
            self.cycle_pneumo() # пневмооборудование
            self.cycle_physics() # физика
            self.cycle_control_wires() # поездные провода
            self.update_ars() # АРС-АЛС
            self.cycle_autodrive() # автоведение
            self.update_railcars() # работа с вагонами

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
        idle_rotate_ticks = 12
        
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
            if self.consist_info["km_mapouts"][str(self.km)]["type"] == "accel" and self.controlling_direction != 0 and self.control_wires["rp"] and self.control_wires["ars_fuse"]:
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
            #логика обсчёта РКСУ (без отката на предыдущие позиции)
            self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi*self.transmissional_number*(self.consist_info["rk_mapouts"][str(self.rk)]["coil_engagement"]/100 if "coil_engagement" in self.consist_info["rk_mapouts"][str(self.rk)] else 1)

            if self.consist_info["km_mapouts"][str(self.km)]["type"] == "accel":

                #сбор схемы на ход

                if self.controlling_direction != 0 and self.control_wires["rp"] and self.control_wires["ars_fuse"]:
                    if str(self.rk) != "0": # если РК != 0, то подать напряжение
                        self.engine_voltage = self.consist_info["rk_mapouts"][str(self.rk)]["voltage"] 
                    
                    if self.consist_info["km_mapouts"][str(self.km)]["target_rk"] > self.rk: # если РК < целевого, то...

                        self.control_wires["rk_spin"] = True # провод вращения РК +

                        switch_current = self.consist_info["rk_mapouts"][str(self.rk)]["switch_current"]/(int(self.control_wires["slow_accel"])+1)

                        if (switch_current > self.engine_current 
                            and self.rk_timer <= 0): 
                                # если ток ниже границы и вышел таймер РК, то обновить таймер и провернуть РК на одну позицию вперёд
                                self.rk_timer = self.consist_info["km_mapouts"][str(self.km)]["switch_time"]
                                self.rk += 1
                    else:
                        self.control_wires["rk_spin"] = False # провод вращения РК -
                else: # иначе если реверс не + или -, то сборсить таймер РК и напряжение на двигателях
                    self.rk_timer = 0
                    self.engine_voltage = 0

                self.traction_direction = self.controlling_direction*sign(self.engine_voltage) #направление тяги

                if self.velocity_direction == 0: 
                    self.velocity_direction = self.traction_direction

                self.engine_current = (abs(self.engine_voltage)-(self.electromotive_force*self.traction_direction*self.velocity_direction))/self.engine_resistance 

                if self.engine_current <= 0: # если ток упал ниже нуля, приравнять нулю...
                    self.engine_current = 0
                    if self.rk_timer > idle_rotate_ticks: self.rk_timer = idle_rotate_ticks # ...и урезать таймер, если надо.

                if self.engine_current >= self.consist_info["peril_current"]: # это для РП
                    self.control_wires["rp"] = False
                    self.engine_current = 0
                    self.engine_voltage = 0

                self.engine_power = abs(self.engine_voltage)*self.engine_current*(self.velocity_direction*self.traction_direction) if self.engine_current > 0 and self.control_wires["rp"] else 0
            elif self.consist_info["km_mapouts"][str(self.km)]["type"] == "brake":
                # режим торможения

                # электродинамическое торможение
                
                if self.controlling_direction != 0 and self.control_wires["rp"]:
                    if str(self.rk) != "0": # если РК != 0, то создать балластное сопротивление
                        self.ballast_resistance = self.consist_info["rk_mapouts"][str(self.rk)]["resistance"]
                    
                    if self.consist_info["km_mapouts"][str(self.km)]["target_rk"] < self.rk: # если РК > целевого, то...

                        self.control_wires["rk_spin"] = True # провод вращения РК +

                        if (self.consist_info["rk_mapouts"][str(self.rk)]["switch_current"] > self.engine_current 
                            and self.rk_timer <= 0): 
                                # если ток ниже границы и вышел таймер РК, то обновить таймер и провернуть РК на одну позицию назад
                                self.rk_timer = self.consist_info["km_mapouts"][str(self.km)]["switch_time"]
                                self.rk -= 1
                    else:
                        self.control_wires["rk_spin"] = False # провод вращения РК -
                else: # иначе если реверс не + или -, то сборсить таймер РК и напряжение на двигателях
                    self.rk_timer = 0
                    self.engine_voltage = 0
                
                self.engine_current = (abs(self.engine_voltage)-(self.electromotive_force*self.traction_direction*self.velocity_direction))/self.engine_resistance 

                if self.engine_current <= 0: # если ток упал ниже нуля, приравнять нулю...
                    self.engine_current = 0
                    if self.rk_timer > idle_rotate_ticks: self.rk_timer = idle_rotate_ticks # ...и урезать таймер, если надо.

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
        vz_1_cond = 2*(self.control_wires["vz_1"] or self.control_wires["vz_1_km"])-1
        self.vz_1 = (self.vz_1 + vz_1_cond*self.consist_info["valve_params"]["vz_1"][1]) 
        self.vz_1 = (self.vz_1 if self.vz_1 >= 0 else 0)
        self.vz_1 = (self.vz_1 if self.vz_1 <= self.consist_info["valve_params"]["vz_1"][0] else self.consist_info["valve_params"]["vz_1"][0])

        # обсчёт вентиля замещения №2
        vz_2_cond = 2*(self.control_wires["vz_2"] or self.control_wires["vz_2_km"])-1
        self.vz_2 = (self.vz_2 + vz_2_cond*self.consist_info["valve_params"]["vz_2"][1]) 
        self.vz_2 = (self.vz_2 if self.vz_2 >= 0 else 0)
        self.vz_2 = (self.vz_2 if self.vz_2 <= self.consist_info["valve_params"]["vz_2"][0] else self.consist_info["valve_params"]["vz_2"][0])

        # обсчёт вентиля автоведения
        if "ad" in self.consist_info["valve_params"]:
            vz_ad_cond = 2*(self.control_wires["vz_ad"])-1
            self.vz_ad = (self.vz_ad + vz_ad_cond*self.consist_info["valve_params"]["ad"][1]) 
            self.vz_ad = (self.vz_ad if self.vz_ad >= 0 else 0)
            self.vz_ad = (self.vz_ad if self.vz_ad <= self.consist_info["valve_params"]["ad"][0] else self.consist_info["valve_params"]["ad"][0])
            self.control_wires["braking_control"] = bool(self.control_wires["vz_1"]+self.control_wires["vz_1_km"]+self.control_wires["vz_2"]+self.control_wires["vz_2_km"]+self.control_wires["vz_ad"])

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
        brake_friction_energy = wheels*1*self.velocity*(max(self.pressure,self.vz_1,self.vz_2,self.vz_ad)*100000*self.brake_cyllinder_surface)

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

    def cycle_autodrive(self):

        # система АВ (Автоведения)
        # чистейший самопал. попытки базироваться на ПУАВ или КСАУП бессмылсенны, т. к. о них ничего не известно.
        # я попробую сделать специальный подвид АВ, издалека напоминающий ПУАВ-СБПП, но только в девятке, если в девятке.

        if self.control_wires["autodrive"] and self.controlling_direction != 0: #если мы подрубили автоведение...
            
            # попытаемся найти маркер на блоке
            current_block = trains[self.first_car if self.controlling_direction == 1 else self.last_car].autodrive_marker
            current_localized_pos = trains[self.first_car if self.controlling_direction == 1 else self.last_car].local_pos[1]

            # если маркер есть и он реагирует на движение вниз...
            if "down" in current_block and self.controlling_direction == -1:
                
                # если блок тормозной...
                if "brake" in current_block:

                    # разбить блок на смысловые элементы
                    block_params = current_block.split("_")

                    # если состояние отстутствует (вагон только заехал), задать состояние торможения
                    if self.autodrive_state["state"] == None: self.autodrive_state["state"] = "braking"

                    # если состяние НЕ разгонное, КМ -> 0
                    # иначе КМ -> +max
                    if self.autodrive_state["state"] != "accel": self.km = 0
                    elif self.autodrive_state["state"] == "accel": self.km = self.consist_info["max_km"]

                    # обсчёт максимальной скорости с учётом тормозной точки
                    maxspeed = 35
                    maxspeed = self.ars_speed if current_localized_pos > 384 and self.autodrive_state["state"] != "braking" else maxspeed
                    maxspeed = 20 if current_localized_pos > 384 and self.autodrive_state["state"] == "braking" else maxspeed
                    maxspeed = 0 if current_localized_pos > 768 and self.autodrive_state["state"] == "braking" else maxspeed

                    # если превышаем Vmax, запитать провод торможения от АВ (todo: сделать для АВ собственный цилиндр)
                    if self.velocity*3.6 > maxspeed: self.control_wires["vz_ad"] = True
                    else: self.control_wires["vz_ad"] = False

                    # если мы проехали тормозную точку и затормозили, разрешить открыть двери
                    if current_localized_pos >= 512 and self.velocity <= 0 and self.autodrive_state["state"] == "braking":
                        self.autodrive_state["state"] = "open"
                        if block_params[2] == "doorL":
                            self.doors["action_r"] = "open"
                        if block_params[2] == "doorR":
                            self.doors["action_l"] = "open"
                        self.autodrive_state["timer"] = 10*120

                    # если двери закрылись, то установить разгонное состояние
                    if self.autodrive_state["state"] == "closing" and self.doors["r"] == "closed" and self.doors["l"] == "closed":
                        self.autodrive_state["state"] = "accel"
                    
                    # если истёк таймер, закрыть двери
                    if self.autodrive_state["timer"] == 0 and self.autodrive_state["state"] == "open" and not self.control_wires["autodrive_door_delay"]:
                        self.autodrive_state["state"] = "closing"
                        self.doors["action_l"] = "close"
                        self.doors["action_r"] = "close"

                    #вычесть таймер
                    if self.autodrive_state["timer"] > 0: self.autodrive_state["timer"] -= 1
                elif "reverse" in current_block:
                    # если состояние отстутствует (вагон только заехал), задать состояние торможения
                    if self.autodrive_state["state"] == None: self.autodrive_state["state"] = "braking"

                    # если состяние НЕ разгонное, КМ -> 0
                    # иначе КМ -> +max
                    if self.autodrive_state["state"] != "accel": self.km = 0
                    elif self.autodrive_state["state"] == "accel": self.km = self.consist_info["max_km"]

                    # обсчёт максимальной скорости с учётом тормозной точки
                    maxspeed = 35
                    maxspeed = self.ars_speed if self.autodrive_state["state"] != "braking" else maxspeed
                    maxspeed = 20 if current_localized_pos > 384 and self.autodrive_state["state"] == "braking" else maxspeed
                    maxspeed = 0 if current_localized_pos > 768 and self.autodrive_state["state"] == "braking" else maxspeed

                    # если превышаем Vmax, запитать провод торможения от АВ (todo: сделать для АВ собственный цилиндр)
                    if self.velocity*3.6 > maxspeed: self.control_wires["vz_ad"] = True
                    else: self.control_wires["vz_ad"] = False

                    # если мы проехали тормозную точку и затормозили, обернуться
                    if current_localized_pos >= 512 and self.velocity <= 0 and self.autodrive_state["state"] == "braking":
                        self.controlling_direction = 1
                        self.autodrive_state["state"] = "accel"

            elif "up" in current_block and self.controlling_direction == 1:
                
                # если блок тормозной...
                if "brake" in current_block:

                    # разбить блок на смысловые элементы
                    block_params = current_block.split("_")

                    # если состояние отстутствует (вагон только заехал), задать состояние торможения
                    if self.autodrive_state["state"] == None: self.autodrive_state["state"] = "braking"

                    # если состяние НЕ разгонное, КМ -> 0
                    # иначе КМ -> +max
                    if self.autodrive_state["state"] != "accel": self.km = 0
                    elif self.autodrive_state["state"] == "accel": self.km = self.consist_info["max_km"]

                    # обсчёт максимальной скорости с учётом тормозной точки
                    maxspeed = 35
                    maxspeed = self.ars_speed if current_localized_pos < 640 and self.autodrive_state["state"] != "braking" else maxspeed
                    maxspeed = 20 if current_localized_pos < 640 and self.autodrive_state["state"] == "braking" else maxspeed
                    maxspeed = 0 if current_localized_pos < 256 and self.autodrive_state["state"] == "braking" else maxspeed

                    # если превышаем Vmax, запитать провод торможения от АВ (todo: сделать для АВ собственный цилиндр)
                    if self.velocity*3.6 > maxspeed: self.control_wires["vz_ad"] = True
                    else: self.control_wires["vz_ad"] = False

                    # если мы проехали тормозную точку и затормозили, разрешить открыть двери
                    if current_localized_pos <= 512 and self.velocity <= 0 and self.autodrive_state["state"] == "braking":
                        self.autodrive_state["state"] = "open"
                        if block_params[2] == "doorR":
                            self.doors["action_r"] = "open"
                        if block_params[2] == "doorL":
                            self.doors["action_l"] = "open"
                        self.autodrive_state["timer"] = 10*120

                    # если двери закрылись, то установить разгонное состояние
                    if self.autodrive_state["state"] == "closing" and self.doors["r"] == "closed" and self.doors["l"] == "closed":
                        self.autodrive_state["state"] = "accel"
                    
                    # если истёк таймер, закрыть двери
                    if self.autodrive_state["timer"] == 0 and self.autodrive_state["state"] == "open" and not self.control_wires["autodrive_door_delay"]:
                        self.autodrive_state["state"] = "closing"
                        self.doors["action_l"] = "close"
                        self.doors["action_r"] = "close"

                    #вычесть таймер
                    if self.autodrive_state["timer"] > 0: self.autodrive_state["timer"] -= 1
                elif "reverse" in current_block:
                    # если состояние отстутствует (вагон только заехал), задать состояние торможения
                    if self.autodrive_state["state"] == None: self.autodrive_state["state"] = "braking"

                    # если состяние НЕ разгонное, КМ -> 0
                    # иначе КМ -> +max
                    if self.autodrive_state["state"] != "accel": self.km = 0
                    elif self.autodrive_state["state"] == "accel": self.km = self.consist_info["max_km"]

                    # обсчёт максимальной скорости с учётом тормозной точки
                    maxspeed = 35
                    maxspeed = self.ars_speed if current_localized_pos < 640 and self.autodrive_state["state"] != "braking" else maxspeed
                    maxspeed = 20 if current_localized_pos < 640 and self.autodrive_state["state"] == "braking" else maxspeed
                    maxspeed = 0 if current_localized_pos < 256 and self.autodrive_state["state"] == "braking" else maxspeed

                    # если превышаем Vmax, запитать провод торможения от АВ (todo: сделать для АВ собственный цилиндр)
                    if self.velocity*3.6 > maxspeed: self.control_wires["vz_ad"] = True
                    else: self.control_wires["vz_ad"] = False

                    # если мы проехали тормозную точку и затормозили, обернуться
                    if current_localized_pos <= 512 and self.velocity <= 0 and self.autodrive_state["state"] == "braking":
                        self.controlling_direction = -1
                        self.autodrive_state["state"] = "accel"
            else:
                self.autodrive_state["state"] = None
                self.control_wires["vz_ad"] = False

                if self.velocity*3.6 >= self.ars_speed or not(self.control_wires["rp"]):
                    self.km = 0

                else:
                    if self.velocity*3.6+5 < self.ars_speed:
                        self.km = self.consist_info["max_km"]
                    else:
                        self.km = 0
            
            if not self.control_wires["ars_fuse"]: self.control_wires["ars_braking_safety_auto"] = True
            else: self.control_wires["ars_braking_safety_auto"] = False

    def update_door_states(self):
        # блок логики открытия-закрытия дверей

        for side in ["l","r"]:
            if "open" in self.doors[f"sound_{side}"]:
                v, t = self.doors[f"sound_{side}"].split("_")
                if t == "0": self.doors[f"sound_{side}"] = ""
                else: self.doors[f"sound_{side}"] = f"{v}_{int(t)-1}"

        z = list(self.consist_info["door_animation_states"].keys())
        if self.doors["action_r"] == "open" and self.doors["r"] != "open":
            if self.doors["timer_r"] == 0:
                self.doors["r"] = z[z.index(self.doors["r"])+1]
                if self.doors["r"] != "open":
                    self.doors["timer_r"] = self.consist_info["door_animation_states"][self.doors["r"]]
                else:
                    self.doors["action_r"] = None
                    self.doors["sound_r"] = "open_10"
            if self.doors["timer_r"] > 0: self.doors["timer_r"] -= 1
        elif self.doors["action_r"] == "close" and self.doors["r"] != "closed":
            if self.doors["timer_r"] == 0:
                self.doors["r"] = z[z.index(self.doors["r"])-1]
                if self.doors["r"] != "closed":
                    self.doors["timer_r"] = self.consist_info["door_animation_states"][self.doors["r"]]
                else:
                    self.doors["action_r"] = None
                    self.doors["sound_r"] = "close_10"
            if self.doors["timer_r"] > 0: self.doors["timer_r"] -= 1

        if self.doors["action_l"] == "open" and self.doors["l"] != "open":
            if self.doors["timer_l"] == 0:
                self.doors["l"] = z[z.index(self.doors["l"])+1]
                if self.doors["l"] != "open":
                    self.doors["timer_l"] = self.consist_info["door_animation_states"][self.doors["l"]]
                else:
                    self.doors["action_l"] = None
                    self.doors["sound_l"] = "open_10"
            if self.doors["timer_l"] > 0: self.doors["timer_l"] -= 1
        elif self.doors["action_l"] == "close" and self.doors["l"] != "closed":
            if self.doors["timer_l"] == 0:
                self.doors["l"] = z[z.index(self.doors["l"])-1]
                if self.doors["l"] != "closed":
                    self.doors["timer_l"] = self.consist_info["door_animation_states"][self.doors["l"]]
                else:
                    self.doors["action_l"] = None
                    self.doors["sound_l"] = "close_10"
            if self.doors["timer_l"] > 0: self.doors["timer_l"] -= 1

    def update_ars(self):
        # блок логики системы АРС
        # так как нормальной состоятельной документации по системам АРС нет почти никакой,
        # пользуюсь эмпирическим опытом Метростроя и собственной гениальной мыслёй, сооружаю собственное подобие АРС:
        # мАРС 6/1 - "модифицированная [система] Автоматической Регулировки Скорости с 6 частотами и 1 одновременно подаваемой"
        # -допустимые частоты: 0-ОЧ-40-60-70-80
        # -срыв предохранителя происходит при превышении допустимой скорости
        # -в случае срыва предохраниетеля АРС активируется ВЗ №2 и блокируется управление ходовым режимом от КМ
        # -восстановление возможно только при понижении скорости до допустимой (т. е. нажатие КВТ при превышении ничего не делает)

        if self.control_wires["ars"] and self.controlling_direction != 0: # если блок АРС включён и реверс в ходовой позиции:
            # считать допустимую скорость следующего блока
            if self.controlling_direction == 1: 
                self.ars_speed = trains[self.first_car].signal_velocity_state
            else:
                self.ars_speed = trains[self.last_car].signal_velocity_state

            # обновить поездные провода, отвечающие за отображение скорости
            for speed in [0,20,40,60,70,80]:
                if speed == self.ars_speed: self.control_wires[f"ars_{speed}"] = True
                else: self.control_wires[f"ars_{speed}"] = False

            # с помощью флага в описательном файле состава можно сделать АРС чисто визуальной.
            if not ("ars_only_visual" in self.consist_info and self.consist_info["ars_only_visual"]):
                # проверить скорость и, если она превышена, выбить предохранитель АРС
                # иначе если не превышена и нажата КВТ, то восстановить предохранитель АРС
                if self.velocity*3.6 > self.ars_speed: self.control_wires["ars_fuse"] = False
                elif self.velocity*3.6 <= self.ars_speed and (self.control_wires["ars_braking_safety"] or self.control_wires["ars_braking_safety_auto"]): self.control_wires["ars_fuse"] = True

                # если АРС сработало и КМ не в нейтральной поизиции, то включить лампу ВД
                if self.km != 0 and not self.control_wires["ars_fuse"]: self.control_wires["ars_traction_disable"] = True
                else: self.control_wires["ars_traction_disable"] = False

                # наконец, включить ВЗ №2, если АРС выбито. надеюсь, обойдусь одним проводом...
                # ВЗ №2 выбран на случай реализации ОВТ, которыми можно этот самый АРС будет отключить.
                if not self.control_wires["ars_fuse"]: self.control_wires["vz_2"] = True
                else: self.control_wires["vz_2"] = False
            
        else: # иначе сбросить систему АРС, не трогая предохранитель.
            self.ars_speed = 20
            for speed in [0,20,40,60,70,80]:
                self.control_wires[f"ars_{speed}"] = False
            self.control_wires["ars_traction_disable"] = False
            self.control_wires["ars_speed_equality"] = False
            self.control_wires["ars_direction"] = False
            self.control_wires["vz_2"] = False
                


    def update_graphics_states(self):
        # блок логики обновления лампочек и x-метров
        for elem_id, element in enumerate(self.consist_info["element_mapouts"]):
            if element["type"] == "lamp":
                self.consist_info["element_mapouts"][elem_id]["state"] = self.control_wires[element["connection"]]
            elif element["type"] == "analog_scale":
                value = 0
                if element["connection"] == "velocity": value = round(complex(self.velocity*3.6).real,2)
                elif element["connection"] == "amps": value = round(
                    self.engine_current*self.traction_direction*self.velocity_direction*self.control_wires["rp"],2)
                elif element["connection"] == "volts": value = round(self.engine_voltage*self.control_wires["rp"],2)
                elif element["connection"] == "press": value = round(max(self.vz_1,self.vz_2,self.pressure,self.vz_ad),2)
                elif element["connection"] == "press_tank": value = round(self.tank_pressure,2)

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
            trains[train_id].signed_velocity = self.velocity*self.velocity_direction
            trains[train_id].pos[0]+=round(math.sin(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)
            trains[train_id].pos[1]+=round(math.cos(math.radians(trains[train_id].angle))*self.pixel_velocity*self.velocity_direction,2)