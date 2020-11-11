import motor28BJController as motoc
import imuController as imuc
import ephemerisController as ephmc
import numpy as np
import atexit
import RPi.GPIO as GPIO
import time
import threading
# import matplotlib.pyplot as plt

import pickle


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

class telescopeController : 

    def __init__( self ) :


#        self.azi_ang2pos = [ 3.99751556e-01, -1.86529031e+02,  1.26316356e+04]
#        self.alt_ang2pos = [ 0.39468058, 74.71001291, 56.43329011]

        self.azi_pos2ang = [-4.62751170e-05,  3.66955057e-02, -1.03775351e+01,  1.09988898e+03, -2.23552879e+04]
        self.alt_pos2ang = [-1.81752237e-04,  3.03587368e-02, -1.17957173e+00,  9.70713184e+01, -3.07961007e+01]

        self.params_azi2pos = np.load('data/azi2pos.npy')
        self.params_alt2pos = np.load('data/alt2pos.npy')
        self.params_pos2azi = np.load('data/pos2azi.npy')
        self.params_pos2alt = np.load('data/pos2alt.npy')



        alt_pins =[17, 18, 27, 22]
        self.altMotor = motoc.motor28BJController(alt_pins, 'altitude', limits=[-100, 8500]) #, limits=[0, 8863])
    
        azi_pins = [14, 15, 23, 24]
        self.aziMotor = motoc.motor28BJController(azi_pins, 'azimuth', limits = [0, 12500])

        focus_pins = [5, 6, 12, 13]
        self.focusMotor = motoc.motor28BJController(focus_pins, 'focus') #, limits = [0, 1625])

        self.imu = imuc.imuController()

        self.ephemeris = ephmc.ephemerisController()

        self.moving_alt = False
        self.moving_az  = False

        self.tracking = False
        self.target = ''

        atexit.register(self.exit)

    # Clearer wrapper funcitons for the movement of the motors
    def move_azimuth(self, direction) : 
        return self.aziMotor.move(direction)
    def move_altitude(self, direction) :             
        return self.altMotor.move(direction)

    def move_focus(self, direction) : 
        return self.focusMotor.move(direction)

    # Move both alt and az
    def move_to_altaz(self, alt, az, verbose = False) : 
        
        self.log('Requestd AltAz coordinates: ', alt, az)
        
        if (alt < 0) : 
            self.log('🙅 The target is below the horizon!')
            return False

        self.move_to_azimuth(az, verbose = verbose)
        self.move_to_altitude(alt, verbose = verbose)
    
    @threaded
    def move_to_altitude(self, new_altitude, threshold = 0.06, verbose = False) : 
        """
            Move to a specific altitude angle, if possible. THe threshold is the 
            largest difference between the requested and actual angle after which
            the telescope will stop moving. 0.03 degs = 1.8' (arcmins).
        """    
        self.moving_alt = True
        
        current_altitude = self.imu.get_altitude()
        diff = np.abs(current_altitude - new_altitude) 
#        print(current_altitude)   
        while(diff > threshold and self.moving_alt) :  
        
            if (diff > 5.0) : steps = 2001
            if (diff < 5.0 and diff >= 0.5) : steps = 201
            if (diff < 0.5) : steps = 51
                        
            current_altitude = self.imu.get_altitude() 
            if (verbose) : self.log('Current altitude: ', round(current_altitude, 2), ' => ', round(new_altitude, 2))
            diff = np.abs(current_altitude - new_altitude)
            if (current_altitude > new_altitude) : 
                for i in range(steps) : 
                    ret = self.move_altitude(1)
            if (current_altitude < new_altitude) : 
                for i in range(steps) : 
                    ret = self.move_altitude(-1)

        self.moving_alt = False

        return self.imu.get_altitude() 

    def is_azimuth_available(self, requested_az, verbose = False) : 
        """
            Given the limited range of the telescope, we don't want to over-run
            any hardware limits and break things. 
            
            Here I calculate the angle between the present position
            and the maximum and minimum position as specified by the motor limits.
            I measured the motor position as a funciton of measured IMU azimuth, fit
            that with a polynomial (n=3), which allows for a decent estimation. 
        
        """
        # Where are we now? 
        current_alt, current_az, current_rot = self.imu.get_altaz()

        # Calculate the current possible range of the telescope
        fn = np.poly1d(self.azi_pos2ang)
        angle_now = fn(self.aziMotor.position)
        print('azi test', angle_now)
        angle_max = current_az + (fn(self.aziMotor.limits[0]) - angle_now)
        angle_min = current_az - (angle_now - fn(self.aziMotor.limits[1]))

        # Is the requested azimuth within the predicted range
        if (requested_az < angle_max and requested_az > angle_min) : 
            if (verbose) : print('Azimuth ', round(requested_az, 1), ' is available.')
            return True
        if (verbose) : 
            print('🚨 Azimuth ', round(requested_az, 2), ' is NOT available.')
            if (requested_az < angle_min) : print('🔄 Rotate telescope counter-clockwise')
            if (requested_az > angle_max) : print('🔄 Rotate telescope clockwise')
        return False

    @threaded
    def move_to_azimuth(self, new_azimuth, threshold = 0.1, verbose = False) : 
        """
            Move the telescope to a specific azimuth angle, if possible
        """
        # Make a prediction if we can rotate in azimuth this far
        if (self.is_azimuth_available(new_azimuth, verbose = verbose) == False) : 
            return False

        self.moving_az = True
    
        current_azimuth = self.imu.get_azimuth()
        diff = np.abs(current_azimuth - new_azimuth) 
        while(diff > threshold and self.moving_az) :  
        
            if (diff > 5.0) : steps = 2001
            if (diff < 5.0 and diff >= 0.5) : steps = 201
            if (diff < 0.5) : steps = 51
                        
            current_azimuth = self.imu.get_azimuth()
            if (verbose) : self.log('Current azimuth: ', round(current_azimuth, 2), ' => ', round(new_azimuth, 2) )   
            diff = np.abs(current_azimuth - new_azimuth)
            
            # Iterate the motor, but stop if we hit hardware limits
            if (current_azimuth > new_azimuth) : 
                for i in range(steps) : 
                    if (self.move_azimuth(-1) == False) : return False                    
            if (current_azimuth < new_azimuth) : 
                for i in range(steps) : 
                    if (self.move_azimuth(1) == False) : return False

        self.moving_az = False

        return self.imu.get_azimuth()
    
    
    def ignore_motor_limits(self) :
    
        self.old_azi_limits = self.aziMotor.limits
        self.old_alt_limits = self.altMotor.limits
        self.old_foc_limits = self.focusMotor.limits

        self.aziMotor.limits = [0, 0]
        self.altMotor.limits = [0, 0]
        self.focusMotor.limits = [0, 0]
        
        self.log('Be careful - disabling motor limits!')

    def use_motor_limits(self) : 
        
        self.aziMotor.limits = self.old_azi_limits
        self.altMotor.limits = self.old_alt_limits
        self.focusMotor.limits = self.old_foc_limits
        self.log('Re-enabling the telescope motor limits')

    def stop(self) : 
        self.moving_alt = False
        self.moving_az = False
        self.log('Stopping altitude and azimuth telescope movement')

    def goto_init(self) : 
        """
            Move the telescope to the init position.
        """
        self.move_to_altitude(0, verbose = True)
        #self.altMotor.position = 0 
        self.aziMotor.goto_pos(0)
#        self.aziMotor.position = 0 
        self.log('Moved to the altitude and azimuth zero positions')

    def zero_motor_positions(self) : 
        self.altMotor.position = 0 
        self.aziMotor.position = 0 
        self.log('Zeroing altitude and azimuth motor positions')

    def get_altaz_pos(self) :
        return (self.altMotor.position, self.aziMotor.position)

    def log(self, *txt) : 
        timestr = time.strftime('<%Y-%m-%d %H:%M:%S> ', time.localtime())
        string = ''
        for tx in txt: 
            if (isinstance(tx, float) == True) : tx = round(tx, 2)
            string += str(tx) + ' '
        print(timestr + string)

    def wait(self) : 
        while(self.moving_alt == True and self.moving_az == True) :
            time.sleep(0.1)
                
    #
    #   We have to clean up the GPIOs here, not in the motorController class
    #
    def exit(self) :
        GPIO.cleanup()

    def goto_target(self, target) : 
        self.target = target
        alt, az = self.ephemeris.get_target_altaz(target)
        self.log('Moving telescope to ' + self.target)
        self.move_to_altaz(alt, az, verbose = True)
        
        
    @threaded
    def track_target(self) :

        # alt, az = self.ephemeris.get_target(self.target)

        self.tracking = True
    
        fn_alt2pos = np.poly1d(self.params_alt2pos)
        fn_azi2pos = np.poly1d(self.params_azi2pos)

        fn_pos2alt = np.poly1d(self.params_pos2alt)
        fn_pos2azi = np.poly1d(self.params_pos2azi)

    
        time0 = time.time()
        time1 = time.time()
        lognbr = 0
        delta_time_az = 0.0

        self.log('Starting trackign on ' + self.target)

        while ( self.tracking == True ) :
            delta_time = time1 - time0
            delta_alt, delta_azi = self.ephemeris.get_altaz_rates()

            pos_alt = self.altMotor.position
            pos_azi = self.aziMotor.position

            current_alt = fn_pos2alt(pos_alt)
            current_azi = fn_pos2azi(pos_azi)

            steps_per_second_alt = fn_alt2pos(current_alt + delta_alt) - pos_alt
            steps_per_second_azi = fn_azi2pos(current_azi + delta_azi) - pos_azi

            new_pos_alt = pos_alt + int(steps_per_second_alt * delta_time)
            new_pos_azi = pos_azi + int(steps_per_second_azi * delta_time)
 
            #self.log(pos_alt - new_pos_alt, new_pos_azi - pos_azi)
 
            # Run the motors 
            self.altMotor.goto_pos(new_pos_alt)            
            self.aziMotor.goto_pos(new_pos_azi)            
 
            # Log how the IMU is responding to the tracking
            delta_time_az += delta_time
            oldaz = 0.0
            if (lognbr > 20) :
                alt, az, rot = self.imu.get_altaz()
                diff_az = (az - oldaz) / delta_time_az # * 3600
                ra, dec = self.ephemeris.get_current_radec(alt, az)
                self.log('Tracking IMU Alt/Az ', round(alt, 3), round(az, 3), round(diff_az), ' deg/hour')
                oldaz = az
                lognbr = 0
                delta_time_az = 0
            lognbr += 1

            time0 = time.time()
            time.sleep(0.25)
            time1 = time.time()
            
            
    def measure_azimuth_articulation(self, resolution = 50) : 
        poss = []
        azis = []
        for motor_position in range(self.aziMotor.limits[0], self.aziMotor.limits[1], resolution) : 
            tele.aziMotor.goto_pos(motor_position)
            poss.append(motor_position)
            az = tele.imu.get_azimuth()
            azis.append(az)
            self.log(round(motor_position, 2), round(az, 2))
        np.save('data/azimuth_articulation_positions.npy', poss)    
        np.save('data/azimuth_articulation_angles.npy', azis)

    def measure_altitude_articulation(self, resolution = 50) : 
        poss = []
        alts = []
        # Move to a sensible azimuth position
        self.aziMotor.goto_pos(int(np.mean(self.aziMotor.limits)))
        for motor_position in range(self.altMotor.limits[0], self.altMotor.limits[1], resolution) : 
            tele.altMotor.goto_pos(motor_position)
            poss.append(motor_position)
            alt = tele.imu.get_altitude()
            alts.append(alt)
            self.log(round(motor_position, 2), round(alt, 2))
        np.save('data/altitude_articulation_positions.npy', poss)    
        np.save('data/altitude_articulation_angles.npy', alts)

if False : 

    tele = telescopeController()     
    #tele.aziMotor.goto_pos(7700)
    #tele.altMotor.goto_pos(200)

    #exit()
    #tele.focusMotor.goto_pos(80)
    for i in range(10) : 
        alt0, az0, rot = tele.imu.get_altaz()
        time.sleep(1)
    while True : 

        alt, az, rot = tele.imu.get_altaz()
        tele.log(alt0 - alt, az0 - az)
        time.sleep(1)
    #tele.measure_altitude_articulation()

    #tele.aziMotor.goto_pos(1000)
    #tele.aziMotor.position = 0





    target = 'Sun' 

    #tele.goto_target(target)
    #tele.track_target()
    #exit()
    #for i in range(100) :    
    #while True:  
    alt, az = tele.ephemeris.get_target_altaz(target)
    #tele.move_to_altaz(alt, az, verbose = True)
    #tele.track_target()



    if True : 
        poss = []
        azis = []
        for pp in range(0, 12500, 25) : 
            tele.aziMotor.goto_pos(pp)
            poss.append(pp)
            az = tele.imu.get_azimuth()
            azis.append(az)
            print(round(pp, 2), round(az, 2))
        
        print('azi vs pos')
        params = np.polyfit(azis, poss, 5)
        print(params)

        print('pos vs azi')
        params = np.polyfit(poss, azis, 5)
        print(params)


        exit()

    #fig, ax = plt.subplots()
    #ax.plot(poss, azis)
    #p = np.poly1d(params)
    #ax.set(xlabel = 'Position', ylabel = 'Angle')
    #ax.plot(poss, p(poss))

    #plt.show()
        #pickle.dump( poss , open( '/home/pi/azipos.poss.pickle', 'wb' ) )
        #pickle.dump( azis , open( '/home/pi/azipos.azis.pickle', 'wb' ) )

    if  False : 
        poss = []
        alts = []
        azis = []

        for pp in range(0, 8400, 200) : 
            tele.altMotor.goto_pos(pp)
            poss.append(pp)
            alt, az, rot = tele.imu.get_altaz()
            alts.append(alt)
            print(round(alt, 2), round(az, 2))
            azis.append(az)

        params = np.polyfit(alts, poss, 4)
        print(params)

    exit()

        
    print('hello')
        
    #print('hello')
    # tele.altMotor.goto_pos(-1000)
    alt, az = tele.imu.get_altaz()
    print(alt, az)
    while True : 
        tele.move_to_altaz(30.0, 140, verbose = True)
        tele.move_to_altaz(4.0, 150, verbose = True)

    exit()    



    while True : 
        tele.move_to_altitude(30, verbose = True)
        tele.move_to_altitude(45, verbose = True)

    exit()

    #print(tele.imu.get_azimuth() )




    #while True : 
    #    tele.move_altitude(-1)

    p0 = 245.1119933489049


    #tele.aziMotor.goto_pos(-9000)


    #tele.goto_init()


    #tele.move_to_altitude(45)

    #exit()

    if False : 
        poss = []
        azis = []
        for pp in range(0, 12500, 25) : 
            tele.aziMotor.goto_pos(pp)
            poss.append(pp)
            azis.append(tele.imu.get_azimuth())

        params = np.polyfit(poss, azis, 4)

        pickle.dump( poss , open( '/home/pi/azipos.poss.pickle', 'wb' ) )
        pickle.dump( azis , open( '/home/pi/azipos.azis.pickle', 'wb' ) )

    if  False : 
        poss = []
        alts = []
        azis = []

        for pp in range(0, 8400, 200) : 
            tele.altMotor.goto_pos(pp)
            poss.append(pp)
            alt, az = tele.imu.get_altaz()
            alts.append(alt)
            print(round(alt, 2), round(az, 2))
            azis.append(az)


    #    pickle.dump( poss , open( '/home/pi/altpos.poss.pickle', 'wb' ) )
    #    pickle.dump( alts , open( '/home/pi/altpos.alts.pickle', 'wb' ) )
    #    pickle.dump( azis , open( '/home/pi/altpos.azis.pickle', 'wb' ) )



    #tele.aziMotor.goto_pos(3500)

    #tele.aziMotor.goto_pos(-9000)

    #ral = tele.move_to_altitude(25, verbose = True)
    #raz = tele.move_to_altaz(45, 180, verbose = True)

    #exit()
    #
    #tele.imu.calibrate()

    #exit()
        
    #tele.move_to_altitude(40, verbose=True)
        
    #tele.move_to_azimuth(180, verbose=True)




    #tele.move_to_altaz(45, 180, verbose = True)

    #exit()

    #tele.goto_init()
    #while True:  

    tele.aziMotor.goto_pos(10000)
    exit()


    #tele.altMotor.goto_pos(-2000)
    tele.move_to_altitude(75, verbose = True)
    #tele.move_to_azimuth(0, verbose = True)

    exit()

    #tele.move_to_altitude(0, verbose=True)



    #tele.move_to_altaz(180, 0, verbose = True)
    #exit()

    #tele.imu.calibrate(niter = 4000)        

    while True :
        #tele.move_to_azimuth(180 + 10, verbose = True)
        alt, az = tele.imu.get_altaz(niter = 10)
    #    tele.log(tele.imu.mags[0], tele.imu.mags[1], tele.imu.mags[2])
    #    tele.log(tele.imu.mags2[0], tele.imu.mags2[1], tele.imu.mags2[2])
        tele.log(tele.imu.mags)
        time.sleep(0.1)
    #exit()
        
      
    #tele.focusMotor.goto_pos(-900)  
        
    #exit()
    object = 'Sun' 
    #for i in range(100) :    
    while True:  
        tele.log('Temperature: ', tele.imu.get_temperature())
        alt, az = tele.ephemeris.get_object_altaz(object)
        tele.move_to_altaz(alt, az, verbose = True)
    #    alt, az = tele.imu.get_altaz()
     #   tele.log(alt, az)
        time.sleep(15)

    #    ral = tele.move_to_altitude(alt)
    #    raz = tele.move_to_azimuth(az)
    #    print(object + ': ', round(alt, 2), round(az, 2), 'Telescope: ', round(ral, 2), round(raz, 2))

    #    time.sleep(15)

        
        
        
        