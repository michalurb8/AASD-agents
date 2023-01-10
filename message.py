import json
from enum import Enum
from typing import Optional
import time
import numpy as np
from utils import prepareDefaultLogger
import pandas as pd

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, str):
            return obj
        return json.JSONEncoder.default(self, obj)

class Message():
    class Type(int, Enum):
        UNDEFINED: int = 0
        BROADCAST: int = 1
        INFORM: int = 2
        DANGER: int = 3

    class DangerType(Enum):
        BASIC = 1

    MESSAGE_TYPE = 'msgtype'
    DISTANCE = 'dst'
    POSITION = 'pos'
    HP = 'hp'
    DANGER_LEVEL = 'dglvl'
    DANGER_TYPE = 'dgtype'
    URGENCY = 'urg'
    ADDITIONAL_INFO = 'addinfo'
    SENDER = 'sender'
    RECEIVER = 'receiver'
    ID = 'ID'

    def __init__(self, sender, receiver) -> None:
        self._clear()

        self.sender = str(sender)
        self.receiver = str(receiver)
        self._setId()

    def _setId(self):
        self.msgId = self._getUniqueID()

    def _getUniqueID(self) -> str:
        return f'::sender:{self.sender}::receiver:{self.receiver}::{str(time.time_ns())}'

    def _clear(self):
        self.messageType = Message.Type.UNDEFINED
        self.agentId = None
        self.distance = None
        self.position = None
        self.hp = None
        self.dangerLevel = None
        self.dangerType = None
        self.urgency = None
        self.additionalInfo = None

    def _strMsgType(self) -> str:
        string = Message.MESSAGE_TYPE
        match self.messageType:
            case Message.Type.UNDEFINED:
                string += '::UNDEFINED\n'
            case Message.Type.BROADCAST:
                string += '::BROADCAST\n'
            case Message.Type.INFORM:
                string += '::INFORM\n'
            case Message.Type.DANGER:
                string += '::DANGER\n'
            case _:
                string += '::ERROR_UNKNOWN_TYPE\n'
        return string

    def _strTemplate(self, name, value) -> str:
        if(name is not None):
            return name + '::' + str(value) + '\n'
        return ''

    def __str__(self) -> str:
        ret = ''
        ret += self._strTemplate(Message.SENDER, self.sender)
        ret += self._strTemplate(Message.RECEIVER, self.receiver)
        ret += self._strMsgType()
        ret += self._strTemplate(Message.HP, self.hp)
        ret += self._strTemplate(Message.DANGER_TYPE, self.dangerType)
        ret += self._strTemplate(Message.DANGER_LEVEL, self.dangerLevel)
        ret += self._strTemplate(Message.URGENCY, self.urgency)
        ret += self._strTemplate(Message.DISTANCE, self.distance)
        ret += self._strTemplate(Message.POSITION, self.position)
        ret += self._strTemplate(Message.ADDITIONAL_INFO, self.additionalInfo)
        return ret

    def _checkMsgForDanger(self) -> bool:
        if(self.messageType != Message.Type.DANGER or self.distance is None or self.position is None \
            or self.hp is None or self.dangerLevel is None or self.dangerType is None or self.urgency is None):
            return False
        return True

    def _checkMsgForBroadcast(self) -> bool:
        if(self.messageType != Message.Type.BROADCAST or self.distance is None or self.position is None \
            or self.urgency is None):
            return False
        return True

    def _checkMsgForInform(self) -> bool:
        if(self.messageType != Message.Type.INFORM or self.position is None \
            or self.urgency is None or self.additionalInfo is None):
            return False
        return True

    def checkMessage(self, msgType) -> bool:
        match msgType:
            case Message.Type.BROADCAST:
                return self._checkMsgForBroadcast()
            case Message.Type.INFORM:
                return self._checkMsgForInform()
            case Message.Type.DANGER:
                return self._checkMsgForDanger()
        return False

    def _dump(self, dictionary: dict, key, value):
        if(value is not None):
            dictionary[key] = value

    def _strLogInfo(self) -> str:
        return f'::sender:{self.sender}::receiver:{self.receiver}\n{str(self)}'

    def dump(self, clearAfter=True, logger=None) -> Optional[str|None]:
        """
            Dumping data creates new message id even without clearing. 
        """
        msg = {
            Message.MESSAGE_TYPE: self.messageType
        }
        
        if(self.checkMessage(Message.Type.BROADCAST)):
            self._dump(msg, Message.DISTANCE, self.distance)
            self._dump(msg, Message.URGENCY, self.urgency)
        elif(self.checkMessage(Message.Type.DANGER)):
            self._dump(msg, Message.DISTANCE, self.distance)
            self._dump(msg, Message.HP, self.hp)
            self._dump(msg, Message.DANGER_TYPE, self.dangerType)
            self._dump(msg, Message.DANGER_LEVEL, self.dangerLevel)
            self._dump(msg, Message.URGENCY, self.urgency)
        elif(self.checkMessage(Message.Type.DANGER)):
            self._dump(msg, Message.URGENCY, self.urgency)
        else:
            if(logger is not None):
                logger.info(f'Message {self.msgId} could not be compiled. {self._strLogInfo()}')
            if(clearAfter):
                self._clear()
            self._setId()
            return None

        self._dump(msg, Message.POSITION, self.position)
        self._dump(msg, Message.SENDER, self.sender)
        self._dump(msg, Message.RECEIVER, self.receiver)
        self._dump(msg, Message.ID, self.msgId)
        self._dump(msg, Message.ADDITIONAL_INFO, self.additionalInfo)

        if(logger is not None):
            logger.info(f'COMPILED: Message "{self.msgId}" {self._strLogInfo()}')

        if(clearAfter):
            self._clear()
        self._setId()
        jsonStr = json.dumps(msg, cls=NumpyEncoder)
        return jsonStr

    def load(self, jsonObj: str, logger=None) -> None:
        msg = json.loads(jsonObj)
        self.loadd(msg, logger=logger)

    def loadd(self, dictionary: dict, logger=None) -> None:
        self._clear()
        sender = None
        receiver = None
        id = None
        for key, value in dictionary.items():
            match key:
                case Message.MESSAGE_TYPE:
                    self.messageType = Message.Type(value)
                case Message.DISTANCE:
                    self.distance = np.array(value)
                case Message.POSITION:
                    self.position = np.array(value)
                case Message.HP:
                    self.hp = np.array(value)
                case Message.DANGER_LEVEL:
                    self.dangerLevel = value
                case Message.DANGER_TYPE:
                    self.dangerType = Message.DangerType(value)
                case Message.URGENCY:
                    self.urgency = value
                case Message.ADDITIONAL_INFO:
                    self.additionalInfo = value
                case Message.ID:
                    id = value
                case Message.SENDER:
                    sender = value
                case Message.RECEIVER:
                    receiver = value

        if(sender is None or self.sender != sender or self.receiver != receiver):
            if(logger is not None):
                logger.info(f'MISMATCH: Message received ::{id}::from:{sender}::to:{receiver} but current message ::{self.id} expected ::from:{self.sender}::to:{self.receiver}')
            self._clear()
            return
        if(logger is not None):
            logger.info(f'LOADED: Message "{self.msgId}" {self._strLogInfo()}')

if __name__ == "__main__":
    msg = Message('sender1', 'receiver1')
    msg2 = Message('sender1', 'receiver1')
    logger = prepareDefaultLogger('testLogger', 'testLogger.log')

    msgDict = {
        Message.MESSAGE_TYPE: Message.Type.BROADCAST,
        Message.DISTANCE: np.array(5),
        Message.POSITION: np.array([7, -9]),
        Message.HP: np.array(9.5),
        Message.DANGER_LEVEL: 2,
        Message.DANGER_TYPE: Message.DangerType.BASIC,
        Message.URGENCY: 3,
        Message.ADDITIONAL_INFO: "This is a test message.\nThis is second line of message.",
        Message.SENDER: 'sender1',
        Message.RECEIVER: 'receiver1',
        Message.ID: 'someID',
    }

    msg.loadd(msgDict, logger)
    jsonStr = msg.dump(True, logger)
    msg2.load(jsonStr, logger)

