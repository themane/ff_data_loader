import yaml

def load_configs(_file):
    with open("../resources/" + _file, 'r') as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
    return data