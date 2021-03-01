from garbled_circuit import *
import math

# input 2 bits (secret-shared form): A, B. output 3 bits (secret-shared form): A < B, A == B, A > B
def comparatorCirc():
    # A --NOT1--AND1-- ---------(A < B)
    #   \  ----^    v
    #    \/         XOR--NOT3---(A = B)
    #    /\         ^
    #   /  ----v    |
    # B --NOT2--AND2-- ---------(A > B)
    gc = GarbledCircuit(GateType.CIRCUIT)
    INPUT_BUS_A = gc.insertGate(GateType.INPUT_BUS)
    INPUT_BUS_B = gc.insertGate(GateType.INPUT_BUS)
    not_1 = gc.insertGate(GateType.NOT)
    not_2 = gc.insertGate(GateType.NOT)
    and_1 = gc.insertGate(GateType.AND)
    and_2 = gc.insertGate(GateType.AND)
    xor = gc.insertGate(GateType.XOR)
    not_3 = gc.insertGate(GateType.NOT)
    OUTPUT_BUS_A = gc.insertGate(GateType.OUTPUT_BUS)
    OUTPUT_BUS_B = gc.insertGate(GateType.OUTPUT_BUS)
    OUTPUT_BUS_C = gc.insertGate(GateType.OUTPUT_BUS)

    gc.insertWire(_source=INPUT_BUS_A, _destination=not_1)
    gc.insertWire(_source=INPUT_BUS_B, _destination=not_2)
    gc.insertWire(_source=INPUT_BUS_A, _destination=and_2)
    gc.insertWire(_source=INPUT_BUS_B, _destination=and_1)

    gc.insertWire(_source=not_1, _destination=and_1)
    gc.insertWire(_source=not_2, _destination=and_2)
    gc.insertWire(_source=and_1, _destination=xor)
    gc.insertWire(_source=and_2, _destination=xor)
    gc.insertWire(_source=xor, _destination=not_3)

    gc.insertWire(_source=and_1, _destination=OUTPUT_BUS_A)
    gc.insertWire(_source=not_3, _destination=OUTPUT_BUS_B)
    gc.insertWire(_source=and_2, _destination=OUTPUT_BUS_C)
    return gc

# input 3 bits (secret-shared form): X, Y, C. Output 2 bits (secret-shared form): if C, then Y, X. else X, Y
# a translation from Jonsson paper into a GMW garbled circuit
def exchangeCirc():
    # images available in resources/compare_exchange_logic
    gc = GarbledCircuit(GateType.CIRCUIT)
    INPUT_BUS_A = gc.insertGate(GateType.INPUT_BUS)
    INPUT_BUS_B = gc.insertGate(GateType.INPUT_BUS)
    INPUT_BUS_C = gc.insertGate(GateType.INPUT_BUS)
    not_1 = gc.insertGate(GateType.NOT)
    and_1 = gc.insertGate(GateType.AND)
    and_2 = gc.insertGate(GateType.AND)
    and_3 = gc.insertGate(GateType.AND)
    and_4 = gc.insertGate(GateType.AND)
    xor_1 = gc.insertGate(GateType.XOR)
    xor_2 = gc.insertGate(GateType.XOR)
    OUTPUT_BUS_A = gc.insertGate(GateType.OUTPUT_BUS)
    OUTPUT_BUS_B = gc.insertGate(GateType.OUTPUT_BUS)

    gc.insertWire(_source=INPUT_BUS_C, _destination=not_1)

    gc.insertWire(_source=INPUT_BUS_A, _destination=and_1)
    gc.insertWire(_source=INPUT_BUS_A, _destination=and_2)
    gc.insertWire(_source=INPUT_BUS_B, _destination=and_3)
    gc.insertWire(_source=INPUT_BUS_B, _destination=and_4)

    gc.insertWire(_source=INPUT_BUS_C, _destination=and_1)
    gc.insertWire(_source=not_1, _destination=and_2)
    gc.insertWire(_source=not_1, _destination=and_3)
    gc.insertWire(_source=INPUT_BUS_C, _destination=and_4)

    gc.insertWire(_source=and_1, _destination=xor_2)
    gc.insertWire(_source=and_2, _destination=xor_1)
    gc.insertWire(_source=and_3, _destination=xor_2)
    gc.insertWire(_source=and_4, _destination=xor_1)

    gc.insertWire(_source=xor_1, _destination=OUTPUT_BUS_A)
    gc.insertWire(_source=xor_2, _destination=OUTPUT_BUS_B)
    return gc

# equal-to circuit, logarithmic in depth of AND gates
def equalityCirc(n_bits):
    gc = GarbledCircuit(GateType.CIRCUIT)
    
    if n_bits == 1:
        INPUT_BUS_A = gc.insertGate(GateType.INPUT_BUS)
        INPUT_BUS_B = gc.insertGate(GateType.INPUT_BUS)
        xor_1 = gc.insertGate(GateType.XOR)
        not_1 = gc.insertGate(GateType.NOT)
        OUTPUT_BUS_A = gc.insertGate(GateType.OUTPUT_BUS)

        gc.insertWire(_source=INPUT_BUS_A, _destination=xor_1)
        gc.insertWire(_source=INPUT_BUS_B, _destination=xor_1)
        gc.insertWire(_source=xor_1, _destination=not_1)
        gc.insertWire(_source=not_1, _destination=OUTPUT_BUS_A)
        return gc
    n1 = math.floor(n_bits/2.0)
    n2 = math.ceil(n_bits/2.0)
    gc1 = equalityCirc(n1)
    gc2 = equalityCirc(n2)

    # need enough wires for 2 numbers
    for i in range(2*n_bits):
        gc.insertGate(GateType.INPUT_BUS)
    gc.insertGate(GateType.CIRCUIT, gc1)
    gc.insertGate(GateType.CIRCUIT, gc2)
    and_1 = gc.insertGate(GateType.AND)
    OUTPUT_BUS_A = gc.insertGate(GateType.OUTPUT_BUS)
    # connect most significant bits of each number first
    for i in range(0, 2*n1, 2):
        gc.insertWire(_source=gc.input_busses[i//2], _destination=gc1, _dest_group=i)
        gc.insertWire(_source=gc.input_busses[n_bits + i//2], _destination=gc1, _dest_group=i+1)
    # then least significant bits
    for i in range(0, 2*n2, 2):
        gc.insertWire(_source=gc.input_busses[n1 + i//2], _destination=gc2, _dest_group=i)
        gc.insertWire(_source=gc.input_busses[n_bits + n1 + i//2], _destination=gc2, _dest_group=i+1)

    # merge
    gc.insertWire(_source=gc1, _destination=and_1, _source_group=0)
    gc.insertWire(_source=gc2, _destination=and_1, _source_group=0)
    gc.insertWire(_source=and_1, _destination=OUTPUT_BUS_A)
    # gc.printGatesRecursive()
    return gc