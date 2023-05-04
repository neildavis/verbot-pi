# verbot-pi

A Python (3.7+) program and library to control a 1980s era [Tomy Verbot](https://www.theoldrobots.com/verbot.html) toy robot using a Raspberry Pi, with the addition of AI smart speaker style 'voice assistant' features.

## Background

The idea was to replace the 80s era electronics in the Tomy Verbot with modern technology with the aim that we can benefit in two ways:

1. The Google AIY voice assistant would recognize our spoken requests with much greater accuracy than the notoriously poor 1980s era system.
2. Gain 'smart-speaker' style AI assistant features at the same time.

The intent was to retain all of the other existing mechanical operation parts from the original toy, instead of replacing these with servos, stepper motors etc which would have been a much greater and more expensive project!

## Features

* JSON-RPC server supporting requests over HTTP
* Voice commands supported via [Google AIY Voice Kit 2.0](https://aiyprojects.withgoogle.com/voice/)
* Google Assistant enabled

## Hardware Setup

This project makes use of:

* An original [Tomy Verbot](https://www.theoldrobots.com/verbot.html) toy with functioning motor & gears.
* A [Raspberry Pi Zero W](https://www.raspberrypi.com/products/raspberry-pi-zero-w/). The newer [Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) would be a worthwhile upgrade but has not been tested.
* The 'Voice Bonnnet' and LED button from the [Google AIY Voice Kit 2.0](https://aiyprojects.withgoogle.com/voice/) Note: the complete kit also includes a Pi Zero W
* A [Pololu DRV8835 Dual Motor Driver Kit for Raspberry Pi](https://www.pololu.com/product/2753)
* A [GeeekPi Raspberry Pi GPIO Expansion Board](https://smile.amazon.co.uk/gp/product/B08C4P66HV/)
* Some (very small) [speakers](https://www.amazon.co.uk/sourcing-map-Replacement-Loudspeaker-20mmx30mm/dp/B07LGH4L4J)
* A [Pimoroni OnOff SHIM](https://shop.pimoroni.com/products/onoff-shim) (or similar smart power off solution for the Pi)
* (Optional) a 5V rechargable power source. (e.g. [a USB power bank](https://www.amazon.co.uk/%E3%80%902-Pack%E3%80%91-Miady-Portable-High-Speed-Compatible/dp/B08T1JCXR5?th=1) or similar)

## Software Setup

This project was developed using [Raspberry Pi OS v10](https://en.wikipedia.org/wiki/Raspberry_Pi_OS) which is based on Debian Linux 10 (aka 'Buster') My exact Kernel version is 5.4.51

### Required Libraries

This project requires Python 3.7+ It's recommended that you create and activate a separate [virtual environment (venv)](https://docs.python.org/3/tutorial/venv.html) for the project.

```bash
pip install requests aiohttp jsonrpcserver jsonrpcclient zeroconf google-assistant-library google-auth-oauthlib 
```

You will also need my fork of [apigpio](https://github.com/neildavis/apigpio.git) (not yet on PyPI)

```bash
git clone https://github.com/neildavis/apigpio.git
cd apigpio
python -m pip install .
```

## Technical Information

The following information has been compiled by a combination of reverse engineering and information contained within [Tomy's patent application](https://patents.google.com/patent/US4717364A/en)

### Power Supply

The 3V DC to driver the motor is supplied on the __orange +ve__ wire and __black ground__ wire from the 2x 1.5V 'C' battery compartment. This was fed from the control board to allow polarty reversing. Our Pololu DRV8835 will serve the same purpose.

The 4x 1.5V 'AA' batteries fed 6V DC to the main electronics control board via the __red +ve__ and __black ground__ wires. I did away with this board and power supply, replacing it with a 5V DC supply from the USB Power Bank battery which will power the Raspberry Pi Zero.

Both the 3V & 5V DC supplies are (+ve line) switched by the board behind the front keypad panel (with the eight red 'action' buttons), with the red 5V DC supply also feeding the red power LED in the bottom right corner of the control panel.

### Electo-mechanical operation

Verbot is controlled by a single bi-deirectional 3V DC motor powered from the 2x 1.5V 'C' size batteries, and an intricate set of gears. The direction of the motor is set by the DC voltage polarity. Depending on the direction of the motor, Verbot is operating in one of two mutually exclusive modes:

| Polarity | Motor Direction | Operating Mode |
|----------|-----------------|----------------|
| Normal   | Anti-clockwise  | Interrogation  |
| Reverse  | Clockwise       | Action         |
|||

#### 1. Interrogation mode

During interrogation mode, Verbot is not performing any movement or other actions. It is the default mode upon powering on.

The motor rotating continuously in an anti-clockwise direction drives a drum with 8 cams placed equally around its circumference which in turn activate (and release) one of 8 normally-open switches. These switches correspond to the 8 possible actions that are programmable from the front mounted keypad.

By wiring the switches to complete a circuit their state can be determined by an attached micro-controlller, or in our case a Raspberry Pi through its GPIO interface.

#### 2. Action mode

Verbot enters action mode when the direction of the motor is reversed. A simple clutch mechanism ensures the drum stops rotating and the last switch selected during interrogation mode stays selected. Now the clutch mechanism starts to rotate a shaft within the drum which connects to various planetary gear sets. The set of gears at the selected location when the drum stopped rotating work to perform the associated action. This action will continue until the motor is again reversed to re-enter interrogation mode. Some actions such as the arms have movement limits enforced by limit switches in series which will break the action circuit, and this prompts the controller to automatically reverse the motor to re-enter interrogation mode.

#### 3. Putting it together

To perform a desired action it's important to allow the drum to rotate during interrogation mode until the corresponding switch has been activated to complete the circuit, before reversing the motor to perform the action. This ensures the correct set of planetary gears connected to the shaft are operational and placed in the correct position to perform the desired action.

#### 4. Switching Key

The following table lists the 9 coloured wires in the ribbon cable connecting the controller board to the interrogation switch bank contained within the gearbox & motor housing, and their corresponding actions.

| Colour | Interrogation order | Action / Purpose |
|--------|---------------------|------------------|
| White  | N/A | GND - connected to opposite side of ALL other switches to complete the circuit |
| Purple | 1 | Stop |
| Red    | 2 | Rotate Right |
| Yellow | 3 | Rotate Left |
| Grey   | 4 | Move Forward |
| Blue   | 5 | Move Backwards |
| Brown  | 6 | Arms Down / Put Down |
| Orange | 7 | Arms Up / Pick Up |
| Green  | 8 | Talk |
||||

## GPIO Pin Assignments

This table lists all of the GPIO pin assignments as setup by the software. Some of these are reserved by e.g. the Voice Bonnet & Google's software.
The 'digital input' pins relating to the 'actions' as described in the section above are highlighted in bold as **Verbot**.

| GPIO Pin (BCM) | Physical Pin | Reserved by | Function |
|----------------|--------------|-------------|----------|
|  -             |   1          | Power | 3.3V |
|  -             |   2          | Power | 5V |
|  2             |   3          | I2C1 | I2C Data |
|  -             |   4          | Power | 5V |
|  3             |   5          | I2C1 | I2C Clock |
|  4             |   7          | | |
|  -             |   6          | Power | GND |
|  4             |   7          | On/Off Shim | Shutdown |
| 14             |   8          | Voice Hat | UART TX |
|  -             |   9          | Power | GND |
| 15             |  10          | Voice Hat | UART RX |
| 17             |  11          | On/Off Shim | Power Button |
| 18             |  12          | Voice Hat | PCM Clock |
| 27             |  13          | On/Off Shim | LED |
|  -             |  14          | Power | GND |
| 22             |  15          | **Verbot** | SW Stop |
| 23             |  16          | Voice Hat | ??? |
|  -             |  17          | Power | 3.3V |
| 24             |  18          | - | - |
| 10             |  19          | **Verbot** | SW Rotate Left |
|  -             |  20          | Power | GND |
|  9             |  21          | **Verbot** | SW Forwards |
| 25             |  22          | **Verbot** | SW Reverse|
| 11             |  23          | **Verbot** | SW Put Down |
|  8             |  24          | **Verbot** | SW Pick Up |
|  -             |  25          | Power | GND |
|  7             |  26          | **Verbot** | SW Talk |
|  0             |  27          | I2C0 | EEPROM Data |
|  1             |  28          | I2C0 | EEPROM Clock |
|  5             |  29          | DRV8835 | Motor 1 Dir |
|  -             |  30          | Power | GND |
|  6             |  31          | DRV8835 | Motor 2 Dir |
| 12             |  32          | DRV8835 | Motor 1 PWM |
| 13             |  33          | DRV8835 | Motor 2 PWM |
|  -             |  34          | Power | GND |
| 19             |  35          | Voice Hat | PCM FS |
| 16             |  36          | AIY | AIY activation Button |
| 26             |  37          | **Verbot** | SW Rotate Right |
| 20             |  38          | Voice Hat | PCM In |
|  -             |  39          | Power | GND |
| 21             |  40          | Voice Hat | PCM Out |
|||||
