import smbus
import time
import math

#Initiliazation of I2C bus
bus = smbus.SMBus(1)

address = 0x68       # Sensor I2C address

# Register address from MPU 9255 register map
power_mgmt_1 = 0x6b
gyro_config = 0x1b
gyro_xout_h = 0x43
gyro_yout_h = 0x45
gyro_zout_h = 0x47
accel_config = 0x1c
accel_xout_h = 0x3b
accel_yout_h = 0x3d
accel_zout_h = 0x3f

class Gyro():
    def __init__(self):
        self.bus = smbus.SMBus(1)

        self.address = 0x68       # Sensor I2C address

        # Register address from MPU 9255 register map
        self.power_mgmt_1 = 0x6b
        self.gyro_config = 0x1b
        self.gyro_xout_h = 0x43
        self.gyro_yout_h = 0x45
        self.gyro_zout_h = 0x47
        self.accel_config = 0x1c
        self.accel_xout_h = 0x3b
        self.accel_yout_h = 0x3d
        self.accel_zout_h = 0x3f
    def acquiredata(self):
        gyro_xout = read_word_2c(gyro_xout_h) #We just need to put H byte address
        gyro_yout = read_word_2c(gyro_yout_h) #as we are reading the word data
        gyro_zout = read_word_2c(gyro_zout_h)

        #FIX ME&********
        self.gyro_xout_scaled = gyro_xout / 32.8 #According to the sensitivity you set
        self.gyro_yout_scaled = gyro_yout / 32.8
        self.gyro_zout_scaled = gyro_zout / 32.8

        accel_yout = read_word_2c(accel_yout_h) #as we are reading the word data
        accel_xout = read_word_2c(accel_xout_h) #We just need to put H byte address
        accel_zout = read_word_2c(accel_zout_h)

        self.accel_xout_scaled = accel_xout / 2048.0 #According to the sensitivity you set
        self.accel_yout_scaled = accel_yout / 2048.0
        self.accel_zout_scaled = accel_zout / 2048.0
        self.startaq = time.time()
    def getyaw(self):
            delta = (time.time() - self.startaq) * self.gyro_zout_scaled
            return delta
    def getroll(self):
            delta = (time.time() - self.startaq) * self.gyro_yout_scaled
            return delta
    def getpitch(self):
            delta = (time.time() - self.startaq) * self.gyro_xout_scaled
            return delta
    def x_angle(self):
        angle = math.atan(self.accel_xout_scaled/math.sqrt(self.accel_yout_scaled**2 + self.accel_zout_scaled**2))*180/math.pi
        return angle
    def y_angle(self):
        angle = math.atan(self.accel_yout_scaled/math.sqrt(self.accel_xout_scaled**2 + self.accel_zout_scaled**2))*180/math.pi
        return angle
    def z_angle(self):
        angle = math.atan(math.sqrt(self.accel_xout_scaled**2 + self.accel_yout_scaled**2)/self.accel_zout_scaled)*180/math.pi
        return angle


# Setting power register to start getting sesnor data
bus.write_byte_data(address, power_mgmt_1, 0)

# Setting Acceleration register to set the sensitivity
# 0,8,16 and 24 for 16384,8192,4096 and 2048 sensitivity respectively
bus.write_byte_data(address, accel_config, 24)

# Setting gyroscope register to set the sensitivity
# 0,8,16 and 24 for 131,65.5,32.8 and 16.4 sensitivity respectively
bus.write_byte_data(address, gyro_config, 24)

def read_byte(adr):
    return bus.read_byte_data(address, adr)

def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val

def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val
def checkpos(pose):

    gyro_xout = read_word_2c(gyro_xout_h) #We just need to put H byte address
    gyro_yout = read_word_2c(gyro_yout_h) #as we are reading the word data
    gyro_zout = read_word_2c(gyro_zout_h)

    #FIX ME&********
    gyro_xout_scaled = gyro_xout / 32.8 #According to the sensitivity you set
    gyro_yout_scaled = gyro_yout / 32.8
    gyro_zout_scaled = gyro_zout / 32.8

    accel_xout = read_word_2c(accel_xout_h) #We just need to put H byte address
    accel_yout = read_word_2c(accel_yout_h) #as we are reading the word data
    accel_zout = read_word_2c(accel_zout_h)

    accel_xout_scaled = accel_xout / 2048.0 #According to the sensitivity you set
    accel_yout_scaled = accel_yout / 2048.0
    accel_zout_scaled = accel_zout / 2048.0
    #R for at rest
    position = "R"
    activity = "R"
    angle = math.atan(accel_yout_scaled/math.sqrt(accel_xout_scaled**2 + accel_zout_scaled**2))*180/math.pi
    if (angle < -35 and math.sqrt(accel_xout_scaled**2 + accel_yout_scaled**2 + accel_zout_scaled**2) > 1.02): #tilt down
	   position = 0
    elif (angle > 35 and math.sqrt(accel_xout_scaled**2 + accel_yout_scaled**2 + accel_zout_scaled**2) > 1.02): #tilt up
	   position = 1
    if (accel_xout_scaled > .6):
       position = 2
    elif (accel_xout_scaled < -.6):
       position = 3
    if (math.sqrt(accel_xout_scaled**2 + accel_yout_scaled**2 + accel_zout_scaled**2) > 1.08):
        position = 69

    if pose == position: #tilt down
        return True
    else:
        return False

def printloop():
        gyro_xout = read_word_2c(gyro_xout_h) #We just need to put H byte address
        gyro_yout = read_word_2c(gyro_yout_h) #as we are reading the word data
        gyro_zout = read_word_2c(gyro_zout_h)

        #FIX ME&********
        gyro_xout_scaled = gyro_xout / 32.8 #According to the sensitivity you set
        gyro_yout_scaled = gyro_yout / 32.8
        gyro_zout_scaled = gyro_zout / 32.8

        accel_xout = read_word_2c(accel_xout_h) #We just need to put H byte address
        accel_yout = read_word_2c(accel_yout_h) #as we are reading the word data
        accel_zout = read_word_2c(accel_zout_h)

        accel_xout_scaled = accel_xout / 2048.0 #According to the sensitivity you set
        accel_yout_scaled = accel_yout / 2048.0
        accel_zout_scaled = accel_zout / 2048.0

        print "X: ", accel_xout_scaled
        print "Y: ", accel_yout_scaled
        print "Z: ", accel_zout_scaled

        print "X: ", gyro_xout_scaled
        print "Y: ", gyro_yout_scaled
        print "Z: ", gyro_zout_scaled
        time.sleep(.5)
