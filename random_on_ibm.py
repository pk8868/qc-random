from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer, IBMQ, BasicAer
from qiskit.tools.monitor import backend_overview, backend_monitor
import qiskit.tools.jupyter

IBMQ.load_account()

n=5
qr = QuantumRegister(n)
cr = ClassicalRegister(n)
circuit = QuantumCircuit(qr, cr)
circuit.h(qr)
circuit.measure(qr, cr)

for j in range(n):
    circuit.h(qr[j])
circuit.measure(qr, cr)

provider = IBMQ.load_account()
#backend_overview()

backend = provider.backend.ibmq_quito
#backend_monitor(backend)

job = execute(circuit, backend, shots=20, memory=True)
data = job.result().get_memory()

int_data = []
for bitstring in data:
    int_data.append( int(bitstring,2) )
print(int_data)