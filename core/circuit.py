from collections import OrderedDict
from components.resistor import Resistor
from components.voltage_source import VoltageSource
from components.current_source import CurrentSource
from utils.file_parser import parse_spice_file

import numpy as np
import os
import json 
from scipy.sparse.linalg import cg
from scipy.sparse.linalg import LinearOperator

class Circuit:
    def __init__(self, file_path):
        self.file_path = file_path
        self.resistors = []
        self.voltage_sources = []
        self.current_sources = []
        self.nodes = []

    def parse_spice(self):
        """Parse the SPICE file to extract components."""
        with open(self.file_path, 'r') as f:
            for line in f:
                tokens = line.strip().split()
                if not tokens or tokens[0].startswith('.') or tokens[0].startswith('*'):
                    continue  # Ignore comments and directives

                element = tokens[0][0]
                if element == 'R':
                    self.resistors.append(Resistor(tokens[1], tokens[2], float(tokens[3])))
                elif element == 'V':
                    self.voltage_sources.append(VoltageSource(tokens[1], tokens[2], float(tokens[3])))
                elif element == 'I':
                    self.current_sources.append(CurrentSource(tokens[1], tokens[2], float(tokens[3])))


    def _extract_nodes(self):
        """Extract and index unique nodes in the circuit."""
        nodes = []
        for component in self.resistors+self.voltage_sources  + self.current_sources:
            nodes.extend([component.node1, component.node2])
        nodes = list(OrderedDict.fromkeys(nodes))
        if '0' in nodes:
            nodes.remove('0')  # Ground node is not included in calculations
        self.nodes = nodes
        self.node_indices = {node: idx for idx, node in enumerate(nodes)}
    def build_system(self):
        """Build the matrix-free system using a LinearOperator."""
        self._extract_nodes()
        num_nodes = len(self.nodes)
        num_voltage_sources = len(self.voltage_sources)
        total_size = num_nodes + num_voltage_sources

        # Vector J as before
        J = np.zeros(total_size)

        # Populate J with current source contributions
        for current_source in self.current_sources:
            n1, n2 = current_source.node1, current_source.node2
            if n1 != '0':
                J[self.node_indices[n1]] -= current_source.current
            if n2 != '0':
                J[self.node_indices[n2]] += current_source.current

        # Populate J with voltage source contributions
        for idx, voltage_source in enumerate(self.voltage_sources):
            n1, n2 = voltage_source.node1, voltage_source.node2
            voltage_row = num_nodes + idx
            if n1 != '0':
                J[voltage_row] = voltage_source.voltage

        # Define a matrix-free operator for G
        def matvec(v):
            result = np.zeros_like(v)

            # Handle resistor contributions
            for resistor in self.resistors:
                n1, n2 = resistor.node1, resistor.node2
                conductance = resistor.conductance
                if n1 != '0':
                    result[self.node_indices[n1]] += conductance * v[self.node_indices[n1]]
                if n2 != '0':
                    result[self.node_indices[n2]] += conductance * v[self.node_indices[n2]]
                if n1 != '0' and n2 != '0':
                    result[self.node_indices[n1]] -= conductance * v[self.node_indices[n2]]
                    result[self.node_indices[n2]] -= conductance * v[self.node_indices[n1]]

            # Handle voltage source constraints
            for idx, voltage_source in enumerate(self.voltage_sources):
                n1, n2 = voltage_source.node1, voltage_source.node2
                voltage_row = num_nodes + idx
                if n1 != '0':
                    result[voltage_row] += v[self.node_indices[n1]]
                    result[self.node_indices[n1]] += v[voltage_row]
                if n2 != '0':
                    result[voltage_row] -= v[self.node_indices[n2]]
                    result[self.node_indices[n2]] -= v[voltage_row]

            return result

        # Create a LinearOperator
        G_operator = LinearOperator((total_size, total_size), matvec=matvec)
        return G_operator, J

    def solve(self):
        """Solve the circuit using a matrix-free iterative solver."""
        self.parse_spice()
        G_operator, J = self.build_system()

        # Solve using Conjugate Gradient method
        V, info = cg(G_operator, J)

        if info != 0:
            raise RuntimeError("Iterative solver did not converge.")

        # Extract node voltages
        node_voltages = {node: V[idx] for node, idx in self.node_indices.items()}

        # Extract the base name of the input file (e.g., 'circuit2' from 'circuit2.sp')
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]

        # Save results to file with a dynamic name
        result_file_path = f'./results/{base_name}-volt.txt'
        os.makedirs(os.path.dirname(result_file_path), exist_ok=True)  # Ensure the directory exists
        with open(result_file_path, 'w') as convert_file:
            convert_file.write(json.dumps(node_voltages, indent=4))


        return node_voltages