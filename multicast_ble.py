from bluepy.btle import Scanner, DefaultDelegate, Peripheral, AssignedNumbers, BTLEException
import threading, binascii, sys


def DBG(*args):
    msg = " ".join([str(a) for a in args])
    print(msg)

class MyDelegate(DefaultDelegate):

    txUUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

    def __init__(self, addr):
        DefaultDelegate.__init__(self)
	self.id = addr

    # Called by BluePy when an event was received.
    def handleNotification(self, cHandle, data):
	DBG("Received notification from: ", self.id, cHandle, " send data ", binascii.b2a_hex(data))
	self.d = data
        map(self.broadcast, peripherals.values())

    def broadcast(self, p):
    	if(self.id == p.addr):
            return
	with lock:
	    txh = peripherals[p.addr].getCharacteristics(uuid=self.txUUID)[0]
        txh.write(self.d, True)

class BleThread(threading.Thread):
    
    def __init__(self, peripheral_addr):
        threading.Thread.__init__(self)
        self.peripheral_addr = peripheral_addr

    def run(self):
        with lock:
            peripheral = peripherals[self.peripheral_addr]
        try:
            m = MyDelegate(self.peripheral_addr)
            peripheral.setDelegate(m)
            print " Configuring RX to notify me on change"
            peripheral.writeCharacteristic(35, b"\x01\x00", withResponse=True)
            print " Subscribed..."
        except BTLEException:
            print BTLEException.message
        except BaseException:
            print "BaseException caught in Thread"
            print BaseException.message

        while True:
	    try:
                if peripheral.waitForNotifications(1):
                    continue
 	    except BTLEException:
		print "BTLEException caught from peripheral " + peripheral.addr
		print BTLEException.message
		peripheral.disconnect()
		break
	    except BaseException:
		print "BaseException acught from peripheral " + peripheral.addr
		print BaseException.message
		peripheral.disconnect()
		break
	    except Exception:
		print "Caught unknown exception from peripheral " + peripheral.addr
		print Exception.message
		peripheral.disconnect()
		break


_devicesToFind = "Adafruit Bluefruit LE"
peripherals = {}
scanner = Scanner(0)
lock = threading.RLock()

while True:
    devices = scanner.scan(2)
    for d in devices:
        try:
            # If scan returns a known addr that's already in the collection, it means it disconnected
            # Remove record and treat it as new
            # Note, it would be nice to remove a device when it goes offline as opposed to when it comes back
            # To do this I'd need something like a ping...dunno what best practice is
            if d.addr in peripherals:
	        with lock:
                    del peripherals[d.addr]

            for (adtype, desc, value) in d.getScanData():
                if (_devicesToFind in value):
                    try:
                        p = Peripheral(d.addr, "random")
                        print " Created Peripheral object for device: " + d.addr
                        print " Appending " + d.addr + " to list of connected devices"
                    except BTLEException:
                        print BTLEException.message
                        break
                    except Exception:
                        print "Unknown Exception"
                        print Exception.message
                    with lock:
                        peripherals[d.addr] = p
                    t = BleThread(d.addr)
                    t.start()
        except:
            print "Unknown error"
            print sys.exc_info()[0]
