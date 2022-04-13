from qiskit import *

def GenerateRandomFraction(accuracy):
    if accuracy <= 1:
        raise Exception("Accuracy must be higher than 1!")
    qr = QuantumRegister(1)
    cr = ClassicalRegister(accuracy)
    circuit = QuantumCircuit(qr, cr)

    for j in range(accuracy):
        circuit.h(0)
        circuit.measure(0, j)
        circuit.reset(0)

    job = execute(circuit, BasicAer.get_backend('qasm_simulator'), shots=1, memory=True)
    data = job.result().get_memory()

    return int(data[0], 2)
    

def RNG(left, right, accuracy=16):
    if accuracy <= 1:
        raise Exception("Accuracy must be higher than 1!")
    if left >= right:
        raise Exception("Left must be lower than right!")

    ret = GenerateRandomFraction(accuracy)
    
    rrange = abs(right - left)
    ret = ret / (2**accuracy - 1)
    ret = ret * rrange
    ret += left
    return ret
