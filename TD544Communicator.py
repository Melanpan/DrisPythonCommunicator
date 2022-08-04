import logging
import time
import serial
import struct
import binascii

class TD544Communicator:
    log = logging.Logger("MAIN")
    # address is unitID which in our case is just 1
    def __init__(self, serial_port):
        self.serial_port = serial_port

    def print_as_bytes(self, s):
        print(" ".join("{:02x}".format(c) for c in s))z

    def fullTest(self, address: int) -> bytes:
        self.log.info("Sending fullreset")
        command = self.createPacketMsg("F", address);
        print(command)
        
    def poll(self, address: int) -> bytes:
        self.log.info("Sending poll")
        command = self.createPacketMsg("P", address);
        print(self.sendReceive(command))

    def reset(self, address: int) -> bytes:
        self.log.info("Sending reset")
        command = self.createPacketMsg("X", address);
        self.sendReceive(command)
    
    def fullTest(self, address: int):
        command = self.createPacketMsg("F", address);
        print(command)
        self.sendReceive(command)

    def getSerialNumber(self, address: int) -> str:
        command = self.createPacketMsg("Y", address);
        return self.sendReceive(command)
    


    def showTextMessage(self, message:list, address:int):
        messageCmd = "M"
        for rowMessage in message:
            messagecmd += self.toTd544DataStream(rowMessage)
        
        command = self.createPacketMsg(command)
        return self.sendReceive(command)

    def toTd544DataStream(self, message):
        

    def xor(self, s,t):
       return "".join(chr(ord(a)^ord(b)) for a,b in zip(s,t))

    def getDigitStringOfLen(self, digit, reqStrLength):
        zeroPaddedStringBuf = ""
        digitString = str(digit)
        numOfZeroToPad = reqStrLength - len(digitString)
        
        while len(zeroPaddedStringBuf) < numOfZeroToPad:
            zeroPaddedStringBuf = zeroPaddedStringBuf + "0"
        
        zeroPaddedStringBuf = zeroPaddedStringBuf + digitString
        
        if len(zeroPaddedStringBuf) > reqStrLength:
            zeroPaddedStringBuf = zeroPaddedStringBuf[:reqStrLength]
       
        return zeroPaddedStringBuf

    def calculateLPC(self, message):
        """ Honestly, this bit of code is still magic to me but I at least got it to work. """
        checkSum = '\x00'
        for i in range(1, len(message)):
            print(f"c = {checkSum} m = {message[i]} xor = {self.xor(checkSum, message[i])}")
            checkSum = self.xor(checkSum, message[i])
            if message[i] == '\x0f':
                break
        
        checkSum = ord(checkSum) | 0x80
        return binascii.unhexlify(hex(checkSum)[2:]) # I don't know why this works!

    def createPacketMsg(self, command: str, address:int) -> bytes:
        packetMsg = ''
        packetMsg += '\x0e'
        packetMsg += self.getDigitStringOfLen(address, 2)
        packetMsg += self.getDigitStringOfLen(len(command), 4)
        packetMsg += command
        packetMsg += '\x0f'
        
        # Calculate the checksum and append it to packetMsg as bytes
        crc = self.calculateLPC(packetMsg) 
        packetMsg = bytes(packetMsg, "utf-8") + crc

        return packetMsg

    def sendRequest(self, ser, command, writeDelay:float):
        # Original java code was writing itterating over every byte and sending it to the serial
        # Which would allow for a writeDelay to be set between bytes.
        # I'm not sure yet how much we need that functionality.
        ser.write(command)

    def readByteTimeLimited(self, ser, timeout: float):
        while time.time() < timeout:
            readByte = ser.read()
            if readByte != '\uffff':
                return readByte
            time.sleep(25)
        Exception("Time Out occurs before getting checksum data");

    def validateCheckSum(self, response):
        bResult = False
        checksumCalculated = self.calculateLPC(response)
        rxdCheckSum = response[:-1] # response.charAt(response.length() - 1);
        
        if (rxdCheckSum == self.calculateLPC(response)):
            bResult = True
        else:
            self.log.warning(f"CheckSum Error!! Expected = {checksumCalculated} received = {rxdCheckSum}")
        
        return bResult

    def readResponse(self, ser, maxResTime: float):
        start = time.time()
        response = b""
        isStartDetected = False
        isEndDetected = False
        timeout = time.time() + maxResTime

        while time.time() < timeout:
            byteResponse = ser.read()
            response += byteResponse

        return response

            
            # elif byteResponse == '\x0f':
            #     if isStartDetected:
            #         response += byteResponse
            #         response += self.readByteTimeLimited(timeout)
            #         isEndDetected = True
            #         timeout = 0
            # elif byteResponse:
            #     time.sleep(0.25)
            #     break
            # else:
            #     response += byteResponse
        
        duration = time.time() - start;
        self.log.info(f"Duration = {duration}")
        print(response)

        if len(response) == 0:
            self.log.warning("No response starting with protocol <start> tag received !!")
            return None
        
        if not isEndDetected:
            self.log.warning(f"Time Out occurs, Received bytes = {len(response)}")
        
        if not self.validateCheckSum(response):
            self.log.warning(f"Recv checksum failed!")
            return None
        
        self.log.info(f"[COM-RECV] {response.encode('utf-8')}")
        return response.encode("utf-8")
        
    def sendReceive(self, command: str, responseTimeOut=0):
        with serial.Serial(self.serial_port, 115200, timeout=1) as ser:
            self.sendRequest(ser, command, 0)
            return self.readResponse(ser, responseTimeOut +1)

        

com = TD544Communicator('/dev/ttyUSB0')