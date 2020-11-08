import guizero as gui
import telescopeController as tc
import time

def hello() : 
    print('hello')



class appController() : 
    
    def __init__(self) : 

        self.tele = tc.telescopeController()
        self.bkg_color = 'thistle'
        self.slew_steps = 100

        self.app = gui.App(title = 'Lockdown Telescope', layout = 'grid', bg = self.bkg_color, height = 250, width = 600)

        welcome_message = gui.Text(self.app, text=" ", grid=[0, 0])

        spacer_box = gui.Box(self.app, grid = [0, 1], width = 10, height = 'fill')


        button_box = gui.Box(self.app, grid = [1, 1], layout = 'grid')
        button_n = gui.PushButton(button_box, command=self.do_button_n, text= 'N', grid = [1, 0])
        button_s = gui.PushButton(button_box, command=self.do_button_s, text= 'S', grid = [1, 2])
        button_e = gui.PushButton(button_box, command=self.do_button_w, text= 'W', grid = [0, 1])
        button_w = gui.PushButton(button_box, command=self.do_button_e, text= 'E', grid = [2, 1])
        button_f1 = gui.PushButton(button_box, command=self.do_button_f1, text= '<', grid = [0, 3])
        button_f2 = gui.PushButton(button_box, command=self.do_button_f2, text= '>', grid = [2,3])
        self.button_go = gui.PushButton(button_box, command=self.do_button_go, text= 'Go', grid = [1, 1])
        self.button_go.bg = 'green'

        spacer_box = gui.Box(self.app, grid = [2, 1], width = 20, height = 'fill')

        button_box2 = gui.Box(self.app, grid = [3, 1], layout = 'grid')
        self.button_track = gui.PushButton(button_box2, command=self.do_button_track, text= 'Track', grid = [0, 0])
        self.button_imu = gui.PushButton(button_box2, command=self.do_button_imu, text= 'IMU', grid = [0, 1])




        spacer_box = gui.Box(self.app, grid = [4, 1], width = 10, height = 'fill')

        input_box = gui.Box(self.app, grid = [5, 1], align='left') #, width = 'fill', height='fill')
        self.target = gui.TextBox(input_box, text='Jupiter')
        my_name = gui.Text(input_box, text=" ")#, align='left') #, width='fill')
#        self.alt    = gui.Text(input_box, text="Alt:\t 0.0")#, align='left') #, width='fill')
#        self.az     = gui.Text(input_box, text="Az\t 0.0")#, align = 'left')#, width='fill')
#        self.rot    = gui.Text(input_box, text="Rot\t 0.0")#, align = 'left')#, width='fill')
#        self.ra     = gui.Text(input_box, text="RA:\t0.0")#, align = 'left')#, width='fill')
#        self.dec    = gui.Text(input_box, text="Dec:\t 0.0") #, align = 'left')#, width='fill')

        self.info_text_template = "Alt\t {0:.2f}\nAz\t {1:.2f}\nRot\t {2:.2f}\nRA\t {3:.2f}\nDec\t {4:.2f}\nAlt pos\t {5:5d}\nAz pos\t {6:5d}"
        output = self.info_text_template.format(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)
        self.info_text    = gui.Text(input_box, text=output, align = 'left', width='fill')#, width='fill')
        self.info_text.align = 'left'

        spacer_box = gui.Box(self.app, grid = [6, 1], width = 10, height = 'fill')

        button_box3 = gui.Box(self.app, grid = [7, 1], align='left') #, width = 'fill', height='fill')

        self.button_lock = gui.PushButton(button_box3, command=self.do_button_lock, text= 'Unlock')
        self.button_goinit = gui.PushButton(button_box3, command=self.do_button_goinit, text= 'Go init')
        button_reset = gui.PushButton(button_box3, command=self.do_button_reset, text= 'Reset')


        # Continiously update the pointing info
        self.info_text.repeat(1000, self.do_button_imu)

        # Launch the app
        self.app.display()


    def do_button_n(self) : 
        for i in range(self.slew_steps) :                 
            ret = self.tele.move_altitude(-1)

    def do_button_s(self) : 
        for i in range(self.slew_steps) :                 
            ret = self.tele.move_altitude(1)

    def do_button_e(self) : 
        for i in range(self.slew_steps) :                 
            ret = self.tele.move_azimuth(1)

    def do_button_w(self) : 
        for i in range(self.slew_steps) :                 
            ret = self.tele.move_azimuth(-1)

    def do_button_f1(self) : 
        for i in range(self.slew_steps) :                 
            ret = self.tele.move_focus(-1)

    def do_button_f2(self) : 
        for i in range(self.slew_steps) :                 
            ret = self.tele.move_focus(1)
 
    def do_button_lock(self) : 
        if (self.button_lock.text == 'Unlock') : 
            self.button_lock.text = 'Lock'
            self.tele.ignore_motor_limits()
        else : 
            self.button_lock.text = 'Unlock'
 
    def do_button_goinit(self) : 
        if (self.button_goinit.text == 'Go init') : 
            self.button_goinit.text = 'Stop'
            self.tele.goto_init()       
        else : 
            self.tele.stop()
            self.button_goinit.text = 'Go init'
             
 
    def do_button_reset(self) : 
        self.tele.zero_motor_positions()
        self.tele.use_motor_limits()
 
    def do_button_go(self) : 
        if (self.button_go.text == 'Go') : 
            self.button_go.text = 'No'
            self.button_go.bg = 'red'
            time.sleep(0.1)
            if ( self.target.value != 'Target' ) : 
                self.tele.goto_target(self.target.value)
        else : 
            self.tele.moving_alt = False
            self.tele.moving_azi = False
            self.button_go.text = 'Go'
            self.button_go.bg = 'green'

    def do_button_track(self) : 
        self.tele.target == self.target.value
        if (self.tele.tracking == False) : 
            self.tele.track_target()
            self.button_track.text = 'STOP'
            self.button_track.bg = 'red'
        else : 
            self.tele.tracking = False
            self.button_track.text = 'Track'
            self.button_track.bg = self.bkg_color

    #@threaded
    def do_button_imu(self) : 
        alt_pos, az_pos = self.tele.get_altaz_pos()
        # Read the IMU
        alt, az, rot = self.tele.imu.get_altaz()
        # Convert to RA and Dec
        ra, dec = self.tele.ephemeris.get_current_radec(alt, az)
        # Update the GUI
        self.info_text.value = self.info_text_template.format(alt, az, rot, ra, dec, alt_pos, az_pos)
 #       # Wait a sec
#        time.sleep(1) 
    


app = appController()    