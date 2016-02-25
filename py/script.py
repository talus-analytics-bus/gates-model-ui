import sys, json

for line in sys.stdin:
    inputObj = json.loads(line)

inputVar = inputObj['input']
outputVar = inputVar + ',3'

percVal = 0.64

print(json.dumps({'output': outputVar, 'percentage': percVal}))
