import math
import time
import threading
import random

trains = {}

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
    def __init__(self,train_type,params,consist_info,self_id,world):
        global trains

        self.linked_to = []
        self.velocity = 0
        self.angular_velocity = 0
        self.train_type = train_type
        self.wheel_radius = consist_info["wheel_radius"]
        self.mass = consist_info["mass"]
        self.wheel_mass = consist_info["wheel_mass"]
        self.humainzed_velocity = 0

        self.consist_info = consist_info

        self.km = consist_info["default_km"]
        self.tk = consist_info["default_tk"]

        self.energy = 0
        self.engine_voltage = 0
        self.engine_current = 0
        self.electromotive_force = 0
        self.engine_constant = consist_info["engine_constant"]
        self.engine_resistance = consist_info["engine_resistance"]

        pos = [128,256]
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

            if self.consist_info["control_system_type"] == "direct":
                self.electromotive_force = self.engine_constant*self.angular_velocity/2/pi
                engine_power = 0
                if self.consist_info["km_mapouts"][str(self.km)]["type"] == "accel":
                    self.engine_voltage = self.consist_info["km_mapouts"][str(self.km)]["voltage"]
                    self.engine_current = (self.engine_voltage-self.electromotive_force)/self.engine_resistance
                    engine_power = self.engine_voltage*self.engine_current
                
                engine_power*=engines

                kinetic_energy = self.mass*self.velocity**2/2*self.train_amount
                revolutional_energy = self.wheel_mass*self.wheel_radius**2*self.angular_velocity**2/4*wheels
                friction_energy = 0.03*self.wheel_mass*9.81*self.angular_velocity

                self.energy = kinetic_energy+revolutional_energy+engine_power/120-friction_energy/120
                self.velocity = ((2*self.energy*self.wheel_radius**2)/(self.train_amount*self.mass*self.wheel_radius**2+wheels*self.wheel_mass*self.wheel_radius**2/2))**0.5
                self.velocity = complex(self.velocity).real
                self.angular_velocity = self.velocity*self.wheel_radius



            self.humainzed_velocity = self.velocity*120*0.125

            for train_id in self.linked_to:
                trains[train_id].velocity = self.velocity
                trains[train_id].pos[0]+=round(math.sin(math.radians(trains[train_id].angle))*self.velocity*2,2)
                trains[train_id].pos[1]+=round(math.cos(math.radians(trains[train_id].angle))*self.velocity*2,2)

            time.sleep(1/120)