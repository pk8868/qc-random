from qiskit import *
from qiskit.providers.ibmq import least_busy
from qiskit.tools.monitor import job_monitor
import logging
import time
import json

def ConfigCheck():
    try:
        _qclogger.logger.info("Loading account...")
        IBMQ.load_account()
        _qclogger.logger.info("Account loaded succesfully!")
    except:
        _qclogger.logger.error("Loading failed! Loading from token.txt")
        token = open("token.txt","r").readline()
        IBMQ.save_account(token)
        IBMQ.load_account()

def ChooseBackend(NotASimulator=False):
    try:
        _qclogger.logger.info("Selecting backend...")
        provider = IBMQ.get_provider(hub='ibm-q')
        servers = provider.backends(filters=lambda b: "reset" in b.configuration().basis_gates, simulator=False, operational=True)
        leastbusy = least_busy(servers)
        backend = provider.get_backend("{}".format(leastbusy))
        _qclogger.logger.info("Selected {}!".format(leastbusy))
    except:
        _qclogger.logger.error("Selecting backend failed!")
        if NotASimulator == True:
            backend = "No quantum computer is available"
        else:
            backend = BasicAer.get_backend("qasm_simulator")
    return backend

class _QCLogging:
    def __init__(self):
        self.logger = logging.getLogger('QCLogger')
        self.fileHandler = logging.FileHandler(_qcconfig.logFile)
        self.formatter = logging.Formatter('%(asctime)s: %(levelname)s> %(message)s')
        self.fileHandler.setFormatter(self.formatter)

        self.logger.addHandler(self.fileHandler)
        self.logger.setLevel(logging.DEBUG)

class _QCBackend:
    def __init__(self):
        ConfigCheck()
        self.lastChange = time.time()
        self.backend = ChooseBackend()
    def GetBackend(self):
        if (time.time() - self.lastChange > _qcconfig.expireTime):
            self.backend = ChooseBackend()
            self.lastChange = time.time()
        return self.backend

class _QCConfig:
    def __init__(self):
        self.logFile = 'qcrandom.log'
        self.exclusions = []
        self.expireTime = 500

        self.LoadConfig()
        
    def LoadConfig(self):
        with open("config.json", "r") as file:
            config = json.load(file)
            print(config)
            self.logFile = config['Log_File']
            self.exclusions = config['Exclusions']
            self.expireTime = config['Expire']

_qcconfig = _QCConfig()
_qclogger = _QCLogging()
_qcbackend = _QCBackend()

def GetRoundFactor(accuracy):
    return len(str(2**accuracy))

# Generates random number between 0 and 1
def GenerateRandomFraction(accuracy):
    assert accuracy > 1, "Accuracy must be higher than 1!"
    qr = QuantumRegister(1)
    cr = ClassicalRegister(accuracy)
    circuit = QuantumCircuit(qr, cr)

    for j in range(accuracy):
        circuit.h(0)
        circuit.measure(0, j)
        if j < accuracy - 1:
            circuit.reset(0)
    
    job = execute(circuit, _qcbackend.GetBackend(), shots=1, memory=True)
    with open(_qcconfig.logFile, 'a') as file:
        file.write(time.asctime())
        job_monitor(job, interval=5, output=file)
    
    data = job.result().get_memory()
    return round(int(data[0], 2) / (2**accuracy - 1), GetRoundFactor(accuracy))
    
def QCRandom(left, right, accuracy=16):
    assert accuracy > 1, "Accuracy must be higher than 1!"
    assert left < right, "Left must be lower than right!"
    
    ret = GenerateRandomFraction(accuracy) * abs(right - left)  + left
    return round(ret, GetRoundFactor(accuracy))
