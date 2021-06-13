#!/usr/bin/env python
import json
import sys

json_file = sys.argv[1]
key = sys.argv[2]

with open(json_file) as f:
    data = json.loads(f.read())

print(data[key])