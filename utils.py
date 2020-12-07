import json


def file_exists(file_name):
    try:
        f = open(file_name)
        f.close()
        return True
    except FileNotFoundError:
        return False


def read_json(filename):
    with open(filename, 'r') as json_file:
        data = json.load(json_file)

    return data.get('array')


def write_json(array, filename):
    with open(filename, 'w') as json_file:
        json.dump({'array': array}, json_file)
