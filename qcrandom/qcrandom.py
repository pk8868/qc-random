import sys
from qiskit import *
from qiskit.providers.ibmq import least_busy
from qiskit.tools.monitor import job_monitor
import logging
import time
import json
import os
import threading
import io

def ConfigCheck():
    try:
        # try loading an account
        # works only if account was previously saved
        _qclogger.logger.info("Loading account...")
        IBMQ.load_account()
        _qclogger.logger.info("Account loaded succesfully!")
    except Exception:
        try:
            # try loading an account using token in token.txt
            _qclogger.logger.error("Loading failed! Loading from token.txt")
            with open("token.txt","r") as tokenFile:
                token = tokenFile.readline()
                IBMQ.save_account(token)
                IBMQ.load_account()
        except Exception:
            # loading account failed - working without ibmq provider
            _qclogger.logger.error("Loading from token.txt failed!")

def ChooseBackend(NotASimulator=False):
    try:
        _qclogger.logger.info("Selecting backend...")
        provider = IBMQ.get_provider(hub='ibm-q')
        # lambda filters backends without reset gate and exclusions from configuration file
        servers = provider.backends(filters=lambda b: "reset" in b.configuration().basis_gates and not b.configuration().backend_name in _qcconfig.exclusions, simulator=False, operational=True)
        leastbusy = least_busy(servers)
        _qclogger.logger.info(f"Selected {leastbusy}!")
        return leastbusy
    except Exception:
        _qclogger.logger.error("Selecting backend failed!")
        if NotASimulator:
            raise Exception("No quantum computer is available")
        else:
            return BasicAer.get_backend("qasm_simulator")

class _QCLogging:
    def __init__(self):
        self.logger = logging.getLogger('QCLogger')
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s: %(levelname)s> %(message)s')
        self.handlers = []
        self.UpdateHandler()
    def UpdateHandler(self):
        # remove all logging handlers
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)

        # select new handler
        self.FillHandlers()
        
        # add handlers to logger
        for handler in self.handlers:
            self.logger.addHandler(handler)
    def FillHandlers(self):
        self.handlers.clear()

        for file in _qcconfig.logFile:
            if file == 'stdout':
                self.handlers.append(logging.StreamHandler(sys.stdout))
            elif file == 'stderr':
                self.handlers.append(logging.StreamHandler(sys.stderr))
            else:
                self.handlers.append(logging.FileHandler(file))
                
        for handler in self.handlers:
            handler.setFormatter(self.formatter)
        
class _QCBackend:
    def __init__(self):
        ConfigCheck()
        self.lastChange = time.time()
        self.backend = ChooseBackend()
    def GetBackend(self):
        # if backend has expired choose a new backend
        if (time.time() - self.lastChange > _qcconfig.expireTime):
            self.backend = ChooseBackend()
            self.lastChange = time.time()
        return self.backend

class _QCConfig:
    def __init__(self):
        self.logFile = ['qcrandom.log']
        self.exclusions = []
        self.expireTime = 600

        self.bufferSize = 100
        self.bufferAccuracy = 64
        self.bufferRefill = 0.5
        self.CreateFile()
        self.LoadConfig()
    
    # Creates configuration file
    def CreateFile(self):
        if not os.path.exists("config.json"):
            newFile = {
                "Log_File": self.logFile
            }
            with open("config.json", "w") as file:
                file.write(json.dumps(newFile))

    # Loads values from config.json
    def LoadConfig(self):
        with open("config.json", "r") as file:
            config = json.load(file)
            if 'Log_File' in config:
                self.logFile = config['Log_File']
			
            if 'Exclusions' in config:
                self.exclusions = config['Exclusions']

            if 'Expire' in config:
                self.expireTime = config['Expire']

            if 'Buffer' in config:
                if 'Size' in config['Buffer']:
                    self.bufferSize = config['Buffer']['Size']
                if 'Accuracy' in config['Buffer']:
                    self.bufferAccuracy = config['Buffer']['Accuracy']
                if 'Refill' in config['Buffer']:
                    self.bufferRefill = config['Buffer']['Refill']
        self.CheckConfig()

    def CheckConfig(self):
        if isinstance(self.logFile, str):
            self.logFile = [self.logFile]

_qcconfig = _QCConfig()
_qclogger = _QCLogging()
_qcbackend = _QCBackend()
_qcbuffer = []

# Returns main buffer's size
def GetBufferSize():
    return len(_qcbuffer)
    
# User interface for updating configuration file, updates logging file
def LoadConfig():
    _qcconfig.LoadConfig()
    _qclogger.UpdateHandler()
    
# Returns number of digits the random number will be rounded to
def GetRoundFactor(accuracy):
    return len(str(2**accuracy))

# Fills secondary buffer
def GenerateBuffer(accuracy, buffersize):
    assert accuracy > 1, "Accuracy must be higher than 1!"
    assert buffersize > 0, "Buffer size must be higher than 0!"

    # creating a quantum circuit
    qr = QuantumRegister(1)
    cr = ClassicalRegister(accuracy)
    circuit = QuantumCircuit(qr, cr)

    for j in range(accuracy):
        circuit.h(0)
        circuit.measure(0, j)
        # skipping last reset (it doesn't change anything)
        if j < accuracy - 1:
            circuit.reset(0)

    job = execute(circuit, _qcbackend.GetBackend(), shots=buffersize, memory=True)
   
    # Save the results of job_monitor to temporary string stream
    stream = io.StringIO("")
    job_monitor(job, interval=5, output=stream)
    _qclogger.logger.info(stream.getvalue())

    data = job.result().get_memory()

    # clear the buffer and fill it with new data
    _qcthreading.buffer.clear()
    for number in data:
        _qcthreading.buffer.append(round(int(number, 2) / (2**accuracy - 1), GetRoundFactor(accuracy)))
    _qclogger.logger.info(f"Second thread finished working, main buffer size {GetBufferSize()}, secondary buffer size {len(_qcthreading.buffer)}")

# wrapper around GenerateBuffer with accuracy and size specified in _qcconfig
def _QCGenerateBuffer():
    GenerateBuffer(_qcconfig.bufferAccuracy, _qcconfig.bufferSize)

class _QCThreading:
    def __init__(self):
        self.buffer = []
        self.startGenerating()
    # Main function that starts fetching numbers in the background
    def startGenerating(self):
        _qclogger.logger.info(f"Second thread started working, main buffer size {GetBufferSize()}")
        self.thread = threading.Thread(target=_QCGenerateBuffer)
        self.thread.start()
    # The thread is ready if it isn't working and secondary buffer is empty
    def isReady(self):
        return not self.thread.is_alive() and len(self.buffer) == 0
    # Copies values from secondary buffer to the main buffer
    def copyBuffer(self):
        self.thread.join()
        _qcbuffer.extend(_qcthreading.buffer)
        self.buffer.clear()


_qcthreading = _QCThreading()

# Calculates refill threshold as number of items
def GetRefillThreshold():
    return int(_qcconfig.bufferRefill * _qcconfig.bufferSize)

# Returns first number from the buffer and pops it off
def GetNumber():
    number = _qcbuffer[0]
    _qcbuffer.pop(0)
    return number

# Starts second thread / copies values from secondary bufer to the main buffer
def CheckBufferState():
    assert _qcconfig.bufferRefill <= 1.0, "Buffer refill threshold must be lower or equal to 1!"
    assert _qcconfig.bufferRefill >= 0, "Buffer refill threshold must be higher or equal to 0!"
    
    if GetBufferSize() <= GetRefillThreshold():
        # start the second thread only if it isn't working and secondary buffer is empty
        if _qcthreading.isReady():
            _qcthreading.startGenerating()
    # refill main buffer when it's empty
    if GetBufferSize() == 0:
        _qcthreading.copyBuffer()

# Generates random number between 0 and 1 (QCRandom helper function)
def GenerateRandomFraction(accuracy):
    assert accuracy > 1, "Accuracy must be higher than 1!"
    CheckBufferState()
    number = GetNumber()
    return round(number, GetRoundFactor(accuracy))

# Main interface - generates random numbers between left and right
def QCRandom(left, right, accuracy=16):
    assert accuracy > 1, "Accuracy must be higher than 1!"
    assert left < right, "Left must be lower than right!"
    
    ret = GenerateRandomFraction(accuracy) * abs(right - left) + left
    return round(ret, GetRoundFactor(accuracy))
