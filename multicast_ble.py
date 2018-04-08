from bluepy.btle import Scanner, DefaultDelegate, Peripheral, AssignedNumbers, BTLEException
import threading, binascii, sys


def DBG(*args):
    msg = " ".join([str(a) for a in args])
    print(msg)

class MyDelegate(DefaultDelegate):

    def __init__(self, addr):
        DefaultDelegate.__init__(self)
	self.id = addr

    # Called by BluePy when an event was received.
    def handleNotification(self, cHandle, data):
	DBG("Received notification from: ", self.id, cHandle, " send data ", binascii.b2a_hex(data))
	self.d = data

class BleThread(Peripheral, threading.Thread):
    
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    WAIT_TIME = 0.3
    ## @var EXCEPTION_WAIT_TIME
    # Time of waiting after an exception has been raiesed or connection lost
    EXCEPTION_WAIT_TIME = 10
    txUUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

    def __init__(self, peripheral_addr):
        threading.Thread.__init__(self)
	Peripheral.__init__(self, peripheral_addr, addrType = "random")
	self.delegate = MyDelegate(peripheral_addr)
	self.withDelegate(self.delegate)
	self.connected = True
	self.featherState = ""
        print " Configuring RX to notify me on change"
        try:
	    self.writeCharacteristic(35, b"\x01\x00", withResponse=True)
	except BaseException:
	    print "BaseException caught when subscribing to notifications for:  " + self.addr
            print BaseException.message
	    raise

    def run(self):
	print "Starting Thread " + self.addr
        while self.connected:
	    try:
                if self.waitForNotifications(self.WAIT_TIME):
		    if self.featherState != self.delegate.d:
			self.featherState = self.delegate.d
        	        map(self.broadcast, peripherals.values())  # This is where failure occurs
	    except BaseException, e:
		print "BaseException caught: " + e.message	# This is most commonly caught error
		self.connected = False
 	    except BTLEException, e:
		print "BTLEException caught from peripheral " + self.addr
		print BTLEException.message
		if str(e) == 'Device disconnected':
		    print self.addr + " disconnected"
		    self.connected = False
                    # We don't want to call waitForNotifications and fail too often
                    time.sleep(self.EXCEPTION_WAIT_TIME)
		else:
		    raise
	    except Exception:
		print "Caught unknown exception from peripheral " + self.addr
		print Exception.message
		self.connected = False
		break

    def broadcast(self, p):
        if(self.addr == p.addr):
            return
        with lock:
            txh = peripherals[p.addr].getCharacteristics(uuid=self.txUUID)[0]
        try:
	    txh.write(self.featherState, True) # Note, this succeeds
        except BTLEException:
            print BTLEException.message


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
                    t = BleThread(d.addr)
		    with lock:
		        peripherals[d.addr] = t
                    t.start()
        except:
            print "Unknown error"
            print sys.exc_info()[0]
