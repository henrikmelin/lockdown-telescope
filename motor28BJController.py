import RPi.GPIO as GPIO
import atexit, pickle, os, time
import numpy as np

class motor28BJController() : 
    """
    Driver class for the 28BJ-48 stepper motor

    Inputs : 
        pins      The 4 Raspberry Pi GPIO pins that control the motor.
        nickname  A name for the motor that's used to store the absolute position.

    Options: 
        limits    The absolute limits of the motors. This is the extreme limits beyond
                  which things may break.
    """
    def __init__(self, pins, nickname, limits = [0, 0]) : 

        self.pins = pins       
        self.limits = limits
        self.nickname = nickname
        self.savefile = 'motor_position_' + nickname + '.pickle'
        atexit.register(self.exit)

        # Setup the GPIO mode
        GPIO.setmode(GPIO.BCM)

        # Initialise the GPIO pins  
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)

        self.position = 0
        self.counter = 0
  
        # The 28BJ-48 stepper motor sequence
        self.seq = [[1,0,0,1],
                    [1,0,0,0],
                    [1,1,0,0],
                    [0,1,0,0],
                    [0,1,1,0],
                    [0,0,1,0],
                    [0,0,1,1],
                    [0,0,0,1]] 

        # Time between motor engagements
        self.wait_time = 0.8e-3

        # Restore previously saved 
        if (os.path.isfile(self.savefile)) : 
            self.position = pickle.load( open( self.savefile, 'rb' ) )
            print('Loaded existing position for ' + self.nickname + ': ', self.position)

    #
    #   Move the position of the motor 
    #
    def move(self, direction) : 
    
        # Impose hardware limits
        if (np.sum(self.limits) > 0) : 
            if (self.position < self.limits[0] and direction == 1) : 
                return self.warning('Motor ' + self.nickname + ' at maximum - cannot move further')
            if (self.position > self.limits[1] and direction == -1) : 
                return self.warning('Motor ' + self. nickname + ' at minimum - cannot move further')

        # Iterate through the pattern
        for index in range(len(self.pins)) : 
            if (self.seq[self.counter][index] != 0) : GPIO.output(self.pins[index], True)
            else : GPIO.output(self.pins[index], False)


        # Tally up the position of the motor
        self.counter += direction
        if (self.counter >= len(self.seq)) : 
            self.counter = 0
            # Keep track of the absolute position of the motor 
            self.position -= 1
        if (self.counter < 0) : 
            self.counter = len(self.seq) + direction
            # Keep track of the absolute position of the motor 
            self.position += 1
            
        time.sleep(self.wait_time)

    #
    #   Go to a specific motor position
    #
    def goto_pos(self, position) : 
        if (position > self.position) : 
            while (position != self.position) : 
                self.move(-1)
        if (position < self.position) : 
            while (position != self.position) : 
                self.move(1)
    
    #
    #   Some kind of structured warning system
    #    
    def warning(self, message) : 
        # Stop lots of the same messages
        if (self.message != self.previous_warning) :        
            print('🚨 MOTOR WARNING 🚨 ' + message)
        self.previous_warning = message
        return False

    #
    #   Cleanup the GPIO ports and save the motor state
    #
    def exit(self) :     
        print('👋  Cleaning up motor ' +  self.nickname + ' 🧽 ')
        pickle.dump( self.position , open( self.savefile, 'wb' ) )
        # Note that I'm noot cleaning up the GPIOs - I wanna do that only once
        # when we're cleaning up everything - perhaps not the best solution... 
        # GPIO.cleanup()
         

