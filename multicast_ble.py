from bluepy.btle import Scanner, DefaultDelegate, Peripheral, AssignedNumbers, BTLEException
import threading, binascii, sys


def DBG(*args):
    msg = " ".join([str(a) for a in args])
    print(msg)

class MyDelegate(DefaultDelegate):

    def __init__(self, addr, lock):
        DefaultDelegate.__init__(self)
	self.id = addr
	self.lock = lock

    # Called by BluePy when an event was received.
    def handleNotification(self, cHandle, data):
	DBG("Received notification from: ", self.id, cHandle, " send data ", binascii.b2a_hex(data))
	# Set both the object's state to the one received and the global state.
    # This helps me avoid writing to the node that reported the state change
    self.d = data
    # Set the shared state to the recieved state so that others can synch
    global state
    with self.lock:
        state = data


class BleThread(Peripheral, threading.Thread):
    
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    WAIT_TIME = 0.3
    ## @var EXCEPTION_WAIT_TIME
    # Time of waiting after an exception has been raiesed or connection lost
    EXCEPTION_WAIT_TIME = 10
    # We'll write to this
    txUUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

    def __init__(self, peripheral_addr, lock):
        threading.Thread.__init__(self)
        self.lock = lock
        self.txh = self.getCharacteristics(uuid=self.txUUID)[0]
#        global state
        # Create the BluePy objects for this node
    	Peripheral.__init__(self, peripheral_addr, addrType = "random")
    	self.delegate = MyDelegate(peripheral_addr, self.lock)
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
                    # Update state to the one from its delegate object
                    if self.featherState != self.delegate.d:
                        self.featherState = self.delegate.d
        	    
                    # Synchronize the feather's state with the global one
            	    with self.lock:
                        global state
                        # If the feather's state matches the global there's nothing to do
                        # Otherwise, sync 
                        if self.featherState != state:
                    	    try:
                        		txh.write(self.featherState, True) # Note, this succeeds
                        		self.featherState = state
                    	    except BTLEException:
                                print "BTLEException caught when writing state"
                                print BTLEException.message

            except BaseException, e:
                print "BaseException caught: " + e.message      # This is most commonly caught error
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
    		


_devicesToFind = "Adafruit Bluefruit LE"
peripherals = {}
scanner = Scanner(0)
lock = threading.RLock() 
state = ""


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
                    t = BleThread(d.addr, lock)

		    with lock:
		        peripherals[d.addr] = t
                    t.start()
        except:
            print "Unknown error"
            print sys.exc_info()[0]
