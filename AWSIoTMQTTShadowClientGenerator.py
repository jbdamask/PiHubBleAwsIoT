# -*- coding: utf-8 -*-
"""
Classes for AWSIoT Device shadow and Callback container. This is basically the code that comes
with the IoT samples but I turned the client into a class (AWSIoTMQTTShadowClientGenerator)
"""

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient, AWSIoTMQTTClient
import logging, time
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
        print(str(datetime.now()) + " Update the reported state")
        newPayload = '{"state":{"reported":' + deltaMessage + '}}'
        self.deviceShadowInstance.shadowUpdate(newPayload)
        print(str(datetime.now()) + " Sent.")

    # Notification delegate knows how to notify other stuff
    def setNotificationDelegate(self, notificationDelegate):
        self.notificationDelegate = notificationDelegate



class AWSIoTMQTTShadowClientGenerator:

    def __init__(self, host, rootCAPath, certificatePath, privateKeyPath, thingName, clientId, topic, useWebsocket=False):
        self.host = host
        self.rootCAPath = rootCAPath
        self.certificatePath = certificatePath
        self.privateKeyPath = privateKeyPath
        self.useWebsocket = useWebsocket
        self.thingName = thingName
        self.clientId = clientId
        self.topic = topic

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
        self.myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
        # AWSIoTMQTTShadowClient configuration
        self.myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
        self.myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
        self.myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self.myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
        # Connect to AWS IoT
        self.myAWSIoTMQTTShadowClient.connect()
        time.sleep(2)

        # Init and configure AWSIoTMQTTClient. This is so I can publish to non-shadow topics
        self.myAWSIoTMQTTClient = self.myAWSIoTMQTTShadowClient.getMQTTConnection()
        self.myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

        # Subscribe to MQTT topic
        self.myAWSIoTMQTTClient.subscribe(self.topic, 1, self.customMqttCallback)

        # Create a deviceShadow with persistent subscription
        self.deviceShadowHandler = self.myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)
        self.shadowCallbackContainer_Bot = ShadowCallbackContainer(self)

        # Listen on deltas
        self.deviceShadowHandler.shadowRegisterDeltaCallback(self.shadowCallbackContainer_Bot.customShadowCallbackDelta)

        # Create the initial State
        self._desired_state = {}
        self._reported_state = {}
        self._devices = []

    # This is how object will make calls to update its container object
    def setContainerCallback(self, callback):
        self.container_callback = callback


    def shadowUpdate(self, JSONPayload):
        self.deviceShadowHandler.shadowUpdate(JSONPayload, self.genericCallback, 5)

    def publish(self, JSONPayload):
        try:
            self.myAWSIoTMQTTClient.publish(self.topic, JSONPayload, 1)
        except:
            print("Publish error: ")

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
        self.shadowCallbackContainer_Bot.setNotificationDelegate(notificationDelgate)

    # Custom MQTT message callback
    def customMqttCallback(self, client, userdata, message):
        print("Received a new message from the lights topic: ")
        print(message.payload)
        print("from topic: ")
        print(message.topic)
        print("--------------\n\n")
        print("Setting PiHub global state with new value")
        #{"state": {"desired": {"property": "2142019b"}}}
        d = json.loads(message.payload)
        self.container_callback(d["state"]["desired"]["property"])

    def genericCallback(self, payload, responseStatus, token):
        # payload is a JSON string ready to be parsed using json.loads(...)
        # in both Py2.x and Py3.x
        if responseStatus == "timeout":
            print("Update request " + token + " time out!")
        if responseStatus == "accepted":
            payloadDict = json.loads(payload)
            print("~~~~~~~~~~~~~~~~~~~~~~~")
            print("Update request with token: " + token + " accepted!")
            print("property: " + json.dumps(payloadDict))
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        if responseStatus == "rejected":
            print("Update request " + token + " rejected!")