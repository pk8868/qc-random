from qiskit import *

def ConfigCheck():
    try:
        IBMQ.load_account()
    except:
        token = open("token.txt","r").readline()
        IBMQ.save_account(token)
        IBMQ.load_account()

def ChooseBackend():
    try:
        provider = IBMQ.get_provider(hub='ibm-q')
        servers=provider.backends(simulator=False, operational=True)
        leastbusy = least_busy(servers)
        backend = provider.get_backend("{}".format(leastbusy))
    except:
        backend = BasicAer.get_backend("qasm_simulator")
    return backend

# Generates random number between 0 and 1
def GenerateRandomFraction(accuracy):
    assert accuracy > 1, "Accuracy must be higher than 1!"
    qr = QuantumRegister(1)
    cr = ClassicalRegister(accuracy)
    circuit = QuantumCircuit(qr, cr)

    for j in range(accuracy):
        circuit.h(0)
        circuit.measure(0, j)
        circuit.reset(0)

    job = execute(circuit, ChooseBackend(), shots=1, memory=True)
    data = job.result().get_memory()

    return int(data[0], 2) / (2**accuracy - 1)
    
def RNG(left, right, accuracy=16):
    assert accuracy > 1, "Accuracy must be higher than 1!"
    assert left < right, "Left must be lower than right!"
    
    randRange = abs(right - left)
    ret = GenerateRandomFraction(accuracy) * randRange  + left
    return ret
