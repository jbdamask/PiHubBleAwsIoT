from bluepy.btle import Scanner, DefaultDelegate, Peripheral, AssignedNumbers, BTLEException
import threading, binascii, sys, time


def DBG(*args):
    msg = " ".join([str(a) for a in args])
    print(msg)

class MasterState():

    def __init__(self):
	self.addr = ""
	self.state = ""

    def setDevice(self, addr):
	self.addr = addr

    def setState(self, state):
	self.state = state

class MyDelegate(DefaultDelegate):

    def __init__(self, addr):
        DefaultDelegate.__init__(self)
	self.id = addr
	print "    Delegate created for device: " + self.id

    # Called by BluePy when an event was received.
    def handleNotification(self, cHandle, data):
	DBG("Received notification from: ", self.id, cHandle, " send data ", binascii.b2a_hex(data))
	ms.setDevice(self.id)
	ms.setState(data)

class FeatherScanner(threading.Thread):
    
    _devicesToFind = "Adafruit Bluefruit LE"
    knownDevices = set()

    def __init__(self):
	self.scanner = Scanner(0)
	threading.Thread.__init__(self)

    def run(self):
	print "running..."
	while True:
#	    print "Scanning for devices..."
	    devices = self.scanner.scan(5)
	    for d in devices:
                for (adtype, desc, value) in d.getScanData():
                    if (self._devicesToFind in value):
			print "Device found " + d.addr
            	        try:
            	    	    # If scan returns a known addr that's already in the collection, it means it disconnected
                    	    # Remove record and treat it as new
            	    	    # Note, it would be nice to remove a device when it goes offline as opposed to when it comes back
            	    	    # To do this I'd need something like a ping...dunno what best practice is
			    if d.addr in self.knownDevices:
		    		with lock:
		        	    del peripherals[d.addr]
		    	    self.knownDevices.add(d.addr)
			except BaseException:
			    print "Caught BaseException in scanner thread"
			    print BaseException.message
	    time.sleep(20) # Rest a bit before scanning again

		
    def getDevices(self):
	return self.knownDevices

peripherals = {}
#scanner = Scanner(0)
lock = threading.RLock()
fs = FeatherScanner()
ms = MasterState()
txUUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
states = {}
currentState = ""

print "Starting FeatherScanner..."
fs.start()
time.sleep(10) # Wait a bit to initialize


#### Debug
#p1 = Peripheral("cd:38:25:5d:ce:a0", "random")
#m1 = MyDelegate("cd:38:25:5d:ce:a0")
#p1.setDelegate(m1)
#p1.writeCharacteristic(35, b"\x01\x00", withResponse=True)

#p2 = Peripheral("e0:f2:72:20:15:43", "random")
#m2 = MyDelegate("e0:f2:72:20:15:43")
#p2.setDelegate(m2)
#p2.writeCharacteristic(35, b"\x01\x00", withResponse=True)

#peripherals["cd:38:25:5d:ce:a0"] = p1
#peripherals["e0:f2:72:20:15:43"] = p2

#states["cd:38:25:5d:ce:a0"] = ""
#states["e0:f2:72:20:15:43"] = ""
##### /Debug 

time.sleep(10)

while True:
    # Add new Feathers to our list
    dev = fs.getDevices()
    for d in dev:
        try:
	    with lock:
		if d in peripherals:
		    continue
		else:
		    print "Adding Peripheral: " + d
		    p = Peripheral(d, "random")
		    print "   Creating delegate"
		    m = MyDelegate(d)
		    print "   Attaching delgate"
		    p.setDelegate(m)
		    try:
		        print "    Configuring RX to notify me on change"
		        resp = p.writeCharacteristic(35, b"\x01\x00", withResponse=True)
			print "      Registered"
	                peripherals[d] = p
		        states[d] = ""
 	   	    except BaseException:
			print "BaseException caught when configuring notifications"
			print  BaseException.message
		    except BTLEException:
           		print "BTLEException caught when configuring notifications"
          		print BTLEException.message
	except BaseException:
	    print "BaseException caught in main loop when initializing Peripheral"
	    print BaseException.message
	except BTLEException:
	    print "BTLEException caught in main loop"
	    print BTLEException.message
        except Exception:
	    print "Unknown Exception caught in main loop"
	    print Exception.message
        except:
            print "Unknown error"
            print sys.exc_info()[0]

    with lock:
	pKeys = peripherals.keys()
    for pKey in pKeys:
	peripherals[pKey].waitForNotifications(0.3)
	if(pKey == ms.addr):
#	    print "Setting current state to the Master's state"
	    currentState = ms.state # This is the master state. Save it so we can synchronize other peripheral objects
	    states[pKey] = ms.state # Save for later...in case we have multiple masters
	    continue
	for key, val in states.iteritems():
	    if(val != currentState):
		states[key] = currentState # Update state for this peripheral
 	        with lock:
		    pTmp = peripherals[key]
		    txh = pTmp.getCharacteristics(uuid=txUUID)[0] 
		try:
		    txh.write(ms.state, True) # Write state to peripheral
		except BaseException:
	            print "Caught BaseException when trying to write data"
		    print BaseException.message
		except Exception:
		    print "Caught unknown exception: " + Exception.message
