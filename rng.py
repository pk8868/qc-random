from qiskit import *

# right is bit count for now
def RNG(left, right, count):
    n=right
    qr = QuantumRegister(1)
    cr = ClassicalRegister(n)
    circuit = QuantumCircuit(qr, cr)

    for j in range(n):
        circuit.h(0)
        circuit.measure(0, j)
        
    job = execute(circuit, BasicAer.get_backend('qasm_simulator'), shots=count, memory=True)
    data = job.result().get_memory()

    int_data = []
    for bits in data:
        int_data.append( left + int(bits, 2) )
    print(int_data)
    return int_data

RNG(1000, 5, 10)