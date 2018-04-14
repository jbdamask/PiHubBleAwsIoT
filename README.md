# PiHubBle
Code for making Raspberry Pi act as a hub for bluetooth le devices to communicate. Use with https://github.com/jbdamask/TouchBleLights

# ToDo
* Speed things up. There's a delay of about 3 seconds to sync states. This may be due to TouchBleLights code more than this
* Add error handling for when peripherals go offline
* I'm going to change the device name on my Feathers in the future. This will let me better target the ones tracked by PiHub. https://learn.adafruit.com/bluefruit-le-micro-atmega32u4-microcontroller-usb-bluetooth-le-in-one/ble-gap#at-plus-gapdevname
I'll have to change the name to search for in this code

# Bugs
* When new devices come online, their state should be synchronized. It's not happening
