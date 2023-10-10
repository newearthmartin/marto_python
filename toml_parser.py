#!/usr/bin/env python
import sys
import toml

json_file = sys.argv[1]
key = sys.argv[2]

with open(json_file) as f:
    data = toml.loads(f.read())

print(data[key])