import os
import glob

def load():
    for env_file in glob.glob('./*.env'):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if not line:
                    continue
                name, value = line.split('=', 1)
                os.environ[name] = value
