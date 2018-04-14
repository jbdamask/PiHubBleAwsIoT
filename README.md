# PiHubBle
Code for making Raspberry Pi act as a hub for bluetooth le devices to communicate. Use with https://github.com/jbdamask/TouchBleLights

# ToDo
* Speed things up. There's a delay of about 3 seconds to sync states. This may be due to TouchBleLights code more than this
* Add error handling for when peripherals go offline

# Bugs
* When new devices come online, their state should be synchronized. It's not happening
