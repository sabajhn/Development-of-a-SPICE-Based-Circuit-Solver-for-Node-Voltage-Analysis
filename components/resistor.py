class Resistor:
    def __init__(self, node1, node2, resistance):
        self.node1 = node1
        self.node2 = node2
        self.resistance = resistance
        self.conductance = 1 / resistance
