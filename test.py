import re

pattern = "([0-9]+.[0-9]+.[0-9]+)"
utilFile = 'gonha/util.py'
version = 'nothing'
with open(utilFile, 'r') as f:
    for line in f.readlines():
        searchObj = re.search(pattern, line)
        if searchObj:
            version = searchObj.group()
            break

print(version)