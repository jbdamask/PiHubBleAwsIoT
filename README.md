# PiHubBle

Turns a Raspberry Pi into a hub for Adafruit Feather Bluefruit LE (Bluetooth low energy) devices.
When run, it will scan the area for Feathers, register them and set their respective states to a shared global.
The idea is that one or more of the registered Feathers act as a master and can set the state for all others.
So, for example, combine this with a Feather running https://github.com/jbdamask/TouchBleLights.

This code also adds AWS IOT functionality so that multiple PiHubs can talk via MQTT

## Synopsis

```
$ sudo python multicast_ble.py
```
To run on boot, do the following:
```chmod +x multicast_ble.py ```
```
$ sudo nano /etc/rc.local
Add lines before exit(0):
	/home/pi/Documents/PiHubBle/multicast_ble.py &
```

## Materials

* https://www.adafruit.com/product/3055
* https://www.adafruit.com/product/1995
* https://www.adafruit.com/product/2692

## Software

* [Bluepy](https://github.com/IanHarvey/bluepy)
* https://github.com/mkieboom/raspberrypi-bluez (Nice Ansible script to update the old version of bluez that comes with Raspian)
* [AWS IoT Core](https://aws.amazon.com/iot-core/)
* [AWS IOT Python SDK](https://github.com/aws/aws-iot-device-sdk-python)

## Troubleshooting

The biggest PITA for me was figuring out the handle for RX notifications. [This post](https://github.com/IanHarvey/bluepy/issues/83) describes how to find it. My notes (for posterity):

> Turn on hcidump and run bluetoothctl. Connect to Feather, select the RX characteristic and set notify on. Then touch a wire (to send data). Hopefully, I’ll see how it turned on notifications.
> YES!!!!
> The hcidump showed me this:
```2017-07-29 14:29:03.106911 < ACL data: handle 64 flags 0x00 dlen 9
    ATT: Write req (0x12)
      handle 0x0023 value  0x01 0x00
```
> 0x0023 is 35
> Add this to my code and it works
```print(self.p.writeCharacteristic(35, b"\x01\x00", withResponse=True))```

> So what is 35? Well according to btle.py for this feather, UART handles can be between 31 and 38. I've seen 37 documented elsewhere, which caused me hours of pain
```
Service <uuid=6e400001-b5a3-f393-e0a9-e50e24dcca9e handleStart=31 handleEnd=38> :
    Characteristic <6e400003-b5a3-f393-e0a9-e50e24dcca9e>, hnd=0x20, supports NOTIFY
    Characteristic <6e400002-b5a3-f393-e0a9-e50e24dcca9e>, hnd=0x24, supports WRITE
```

## Authors

* **John B Damask** [Repos](https://github.com/jbdamask)


## ToDo
* Lots

## Bugs
* Many (coding for learning/information at this point)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Kudos

* [Adafruit](http://www.adafruit.com) is awesome. Buy your products from them (I don't work there)
* [Ian Harvey](https://github.com/IanHarveyhttps://github.com/IanHarvey)
