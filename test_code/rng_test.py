from distutils.log import log
from qiskit import *
import math
# right is bit count for now
def RNG(left, right, count):
    range = right - left
    n = math.ceil(math.log(range, 2))
    print(n)
    qr = QuantumRegister(1)
    cr = ClassicalRegister(right)
    circuit = QuantumCircuit(qr, cr)
    
    for j in range(right):
        circuit.h(0)
        circuit.measure(0, j)
        circuit.reset(0)
    print(circuit.draw())
    job = execute(circuit, BasicAer.get_backend('qasm_simulator'), shots=count, memory=True)
    data = job.result().get_memory()

    int_data = []
    for bits in data:
        int_data.append( left + int(bits, 2) )
    return int_data

print(RNG(0, 255, 10))