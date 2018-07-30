# -*- coding: utf-8 -*-
"""
Classes for AWSIoT Device shadow and Callback container. This is basically the code that comes
with the IoT samples but I turned the client into a class (AWSIoTMQTTShadowClientGenerator)


Todo:
    * I need to more the device dictionary initial state to another class...doesn't belong here

"""

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import json
from datetime import datetime


class ShadowCallbackContainer:

    def __init__(self, deviceShadowInstance):
        self.deviceShadowInstance = deviceShadowInstance

    # Custom Shadow callback
    def customShadowCallbackDelta(self, payload, responseStatus, token):
        # payload is a JSON string ready to be parsed using json.loads(...)
        # in both Py2.x and Py3.x
        print(str(datetime.now()) + " Received a delta message:")
        payloadDict = json.loads(payload)
        deltaMessage = json.dumps(payloadDict["state"])
        print(str(datetime.now()) + " " + deltaMessage)
        # update the device using our NotificationHandler delegate object
        self.notificationDelegate.notify(payload)
        print(str(datetime.now()) + " Update the reported state")
        newPayload = '{"state":{"reported":' + deltaMessage + '}}'
        self.deviceShadowInstance.shadowUpdate(newPayload, None, 5)
        print(str(datetime.now()) + " Sent.")

    # Notification delegate knows how to notify other stuff
    def setNotificationDelegate(self, notificationDelegate):
        self.notificationDelegate = notificationDelegate


class AWSIoTMQTTShadowClientGenerator:

    def __init__(self, host, rootCAPath, certificatePath, privateKeyPath, thingName, clientId, useWebsocket=False):
        self.host = host
        self.rootCAPath = rootCAPath
        self.certificatePath = certificatePath
        self.privateKeyPath = privateKeyPath
        self.useWebsocket = useWebsocket
        self.thingName = thingName
        self.clientId = clientId

        if useWebsocket and certificatePath and privateKeyPath:
            print("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
            exit(2)

        if not useWebsocket and (not certificatePath or not privateKeyPath):
            print("Missing credentials for authentication.")
            exit(2)

        # Configure logging
        logger = logging.getLogger("AWSIoTPythonSDK.core")
        logger.setLevel(logging.INFO)
        streamHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)

        # Init AWSIoTMQTTShadowClient
        self.myAWSIoTMQTTShadowClient = None
        if useWebsocket:
            self.myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId, useWebsocket=True)
            self.myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
            self.myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
        else:
            self.myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
            self.myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
            self.myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

        # AWSIoTMQTTShadowClient configuration
        self.myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self.myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect to AWS IoT
        self.myAWSIoTMQTTShadowClient.connect()

        # Create a deviceShadow with persistent subscription
        self.deviceShadowHandler = self.myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)
        self.shadowCallbackContainer_Bot = ShadowCallbackContainer(self.deviceShadowHandler)

        # Listen on deltas
        self.deviceShadowHandler.shadowRegisterDeltaCallback(self.shadowCallbackContainer_Bot.customShadowCallbackDelta)

        # Create the initial State
        self._desired_state = {}
        self._reported_state = {}
        self._devices = []

    def shadowUpdate(self, JSONPayload, shadow_callback, wtf):
        self.deviceShadowHandler.shadowUpdate(JSONPayload, shadow_callback, wtf)


    def getState(self):
        _r = '"reported": {"ble_devices":' + json.dumps(self._reported_state.values()) + '}'
        _d = '"desired": {"ble_devices":' + json.dumps(self._desired_state.values()) + '}'
        return '{"state": {' + _r + ', ' + _d + '} }'


    def updateState(self, value):
        self._reported_state[value["MAC"]] = value
        for x in self._devices:
            self._desired_state[x]["color"] = value["color"]
        print (str(datetime.now()) + " Desired state values: " + json.dumps(self._desired_state.values()))
        print (str(datetime.now()) + " Reported state values: " + json.dumps(self._reported_state.values()))
        return self.getState()


    def registerDeviceAddress(self, address):
        print "AWSIoTMQTTShadowClientGenerator is registering device: " + address
        self._devices.append(address)
        # Initialize dictionary for this BLE device. Set color to off
        self._desired_state[address] = { "MAC": address, "color": "21430000009b"}


    def registerNotificationDelegate(self, notificationDelgate):
        #self.notificationDelgate = notificationDelgate
        self.shadowCallbackContainer_Bot.setNotificationDelegate(notificationDelgate)
