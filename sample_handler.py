import os, json

def save_sample(ret, filename):
        ret = json.dumps(ret, indent=4)
        json_path = os.path.join('request_samples', filename)
        with open(json_path, 'w') as f:
            f.write(ret)

def read_sample(filename):
    json_path = os.path.join('request_samples', filename)
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data