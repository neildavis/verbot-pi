# verbot-pi
A Python program and library to control a Tomy Verbot using a Raspberry Pi

## Verbot Mechanical Operation

The following information has been compiled by a combination of reverse engineering and information contained within [Tomy's patent application](https://patents.google.com/patent/US4717364A/en)

Verbot is controlled by a single bi-deirectional 3V DC motor and a complex set of gears. The direction of the motor is set by the DC voltage polarity. Depending on the direction of the motor, Verbot is operating in one of two mutually exclusive modes:

| Polarity | Motor Direction | Operating Mode |
|----------|-----------------|----------------|
| Normal   | Anti-clockwise  | Interrogation  |
| Reverse  | Clockwise       | Action         |
|||

### 1. Interrogation mode
During interrogation mode, Verbot is not performing any movement or other actions. It is the default mode upon powering on. 

The motor rotating continuously in an anti-clockwise direction drives a drum with 8 cams placed equally around its circumference which in turn activate (and release) one of 8 normally-open switches. These switches correspond to the 8 possible actions that are programmable from the front mounted keypad.

By wiring the switches to complete a circuit their state can be determined by an attached micro-controlller, or in our case a Raspberry Pi through its GPIO interface.

### 2. Action mode
Verbot enters action mode when the direction of the motor is reversed. A simple clutch mechanism ensures the drum stops rotating and the last switch selected during interrogation mode stays selected. Now the clutch mechanism starts to rotate a shaft within the drum which connects to various planetary gear sets. The set of gears at the selected location when the drum stopped rotating work to perform the associated action. This action will continue until the motor is again reversed to re-enter interrogation mode. Some actions such as the arms have movement limits enforced by limit switches in series which will break the interrogation circuit, and this prompts the controller to automatically reverse the motor to re-enter interrogation mode. 

### 3. Putting it together
To perform a desired action it's important to allow the drum to rotate during interrogation mode until the corresponding switch has been activated to complete the circuit, before reversing the motor to perform the action. This ensures the correct set of planetary gears connected to the shaft are operational and placed in the correct position to perform the desired action.

### 4. Switching Key
The following table lists the 9 coloured wires in the ribbon cable connecting the controller board to the interrogation switch bank contained within the gearbox & motor housing, and their corresponding actions. 

| Colour | Interrogation order | Action / Purpose |
|--------|---------------------|------------------|
| White  | N/A | GND - connected to opposite side of ALL other switches to complete the circuit |
| Purple | 1 | Stop |
| Red    | 2 | Rotate Right |
| Yellow | 3 | Rotate Left |
| Grey   | 4 | Move Forward |
| Blue   | 5 | Move Backwards |
| Brown  | 6 | Arms Up / Pick Up |
| Orange | 7 | Arms Down / Put Down |
| Green  | 8 | Talk |
||||
