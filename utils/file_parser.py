from components.resistor import Resistor
from components.voltage_source import VoltageSource
from components.current_source import CurrentSource

def parse_spice_file(file_path):
    """Parse the SPICE file to extract components."""
    components = {
        "resistors": [],
        "voltage_sources": [],
        "current_sources": []
    }
    with open(file_path, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            if not tokens or tokens[0].startswith('.') or tokens[0].startswith('*'):
                continue  # Ignore comments and directives

            element = tokens[0][0]
            if element == 'R':
                components["resistors"].append(Resistor(tokens[1], tokens[2], float(tokens[3])))
            elif element == 'V':
                components["voltage_sources"].append(VoltageSource(tokens[1], tokens[2], float(tokens[3])))
            elif element == 'I':
                components["current_sources"].append(CurrentSource(tokens[1], tokens[2], float(tokens[3])))
    return components