# Lockdown Telescope

Also stuck at home during this lockdown? Let's build a telescope! 

_More to be added!_


## Components
* **A telescope!** I got a second-hand Tasco 57T from the [Oxfam charity shop](https://www.oxfam.org.uk/) in Stratford-Upon-Avon (£15) 

* **A [Raspberry Pi 4](https://shop.pimoroni.com/products/raspberry-pi-4?variant=29157087412307)** - this'll be the brains of the operation. I choose the 4 since it can operate in the [On-The-Go (OTG) mode](https://en.wikipedia.org/wiki/USB_On-The-Go) over USB-C, which means I can plug my computer straight into it instead of connecting via WiFi should I decide to use the telescope away from my back yard once the lockdown ends. The Raspberry Pi Zero does this also, but I figured I could do with more processing power. Regardless, new things are fun. (Pimoroni - £33.90)

* **A camera.** [The Raspberry Pi Camera](https://shop.pimoroni.com/products/raspberry-pi-camera-module-v2-1-with-mount?variant=19833929735) (Pimoroni - £24)

* **Three stepper motors and controller boards.** These will control altitude, azimuth and focus motion on the telescope. I got 28BYJ-48 motor with the ULN2003 motor driver board on eBay for the total price of £8.38! 

* **Two lead screws with fittings.** These will translate the rotating motor motion to a linear motion that will move the telescope up/down (altitude) and left/right (azimuth). I got two 300 mm screws that came with both the nuts and the motor couplers (eBay  - £16.70)

* **An inertial measurement unit (IMU).** This will give the direction that the telescope is pointing in. I use the [ICM20948](https://shop.pimoroni.com/products/icm20948) from Pimoroni's Breakout Garden suite of controllers that has a magnetometer (for the azimuth pointing), a gyroscope and accelerometer (for the altitude posting) (Pimoroni - £13.80)

* **A screen** for a fancy interface and exposure previews. Pimoroni makes this [really cute 240x240 display (ST7789)](https://shop.pimoroni.com/products/1-3-spi-colour-lcd-240x240-breakout) as part of their Breakout Garden. (Pimoroni - £15)

* **Two lazy susans** with bearings for a smooth rotation. (eBay - £5.18)

* **A coupler** that can connect the stepper motor and the focus shaft (eBay - 3.49)

* **A prototyping board** to organise the various connections. The [Adafruit Perma-Proto HAT](https://shop.pimoroni.com/products/adafruit-perma-proto-hat-for-pi-mini-kit?variant=1038451613) is excellent for this (Pimoroni - £4.80)

* **Bits of wood** for the telescope mount. I have quite a bit of 18 mm plywood left over from when I built my kitchen, so will consider it free of charge.


// 33.90 + 24.0 + 15 + 8.38 + 13.80 + 15 + 5.18 + 3.49 + 4.80

## Raspberry Pi GPIO mappings

| GPIO pin | Connects to  | Purpose |
|:----------------:|:-------------:|:-------:|
|        17        | Motor 1 pin 1 | Altitude motor |
|        18        | Motor 1 pin 2 |     -    |
|        27        | Motor 1 pin 3 |     -    |
|        22        | Motor 1 pin 4 |     -    |
|        5         | Motor 2 pin 1 | Azimuth motor |
|        6         | Motor 2 pin 2 |    -     |
|        12        | Motor 2 pin 3 |    -     |
|        13        | Motor 2 pin 4 |    -     |
|        14        | Motor 3 pin 1 |Focus motor|
|        15        | Motor 3 pin 2 |     -    |
|        23        | Motor 3 pin 3 |     -    |
|        24        | Motor 3 pin 4 |     -    |
|        2 (I<sup>2</sup>C - SDA)        | ICM2094      |IMU for pointing information |
|        3 (I<sup>2</sup>C - SCL)        | ICM2094      | - |
|        4 (I<sup>2</sup>C - 1-Wire)        | ICM2094      | - |
| 	 7 (SPI - CS)	| ST7789	| Screen |
| 	 11 (SPI - SCK)	| ST7789	| - |
| 	 10 (SPI - MOSI)	| ST7789	| - |
| 	 9 (SPI - DC)	| ST7789	| - |
| 	 19 (SPI - BL)	| ST7789	| - |






