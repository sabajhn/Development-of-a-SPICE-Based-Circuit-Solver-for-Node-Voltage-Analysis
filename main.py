from core.circuit import Circuit

def main():
    dataset=["testcase17.sp",  "testcase17.sp",  "testcase1.sp",  "testcase3.sp",  "testcase5.sp","testcase12.sp",  "testcase18.sp",  "testcase2.sp",  "testcase4.sp",  "testcase6.sp"]
    # dataset = ['circuit2.sp']  # Replace with the actual SPICE file path
    for f in dataset:
        circuit = Circuit('./dataset/'+f)
    node_voltages = circuit.solve()
    print("Node Voltages:", node_voltages)

if __name__ == "__main__":
    main()