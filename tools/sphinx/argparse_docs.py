boshFileText = ""
with open("../python/boutiques/bosh.py", "r") as boshFile:
    boshFileText = boshFile.read()

boshFunctions = boshFileText.split("\n\n")
nonParserStrings = []
for idx, function in enumerate(boshFunctions):
    if function[5:12] != "parser_":
        nonParserStrings.append(idx)

indexShifter = 0
for nonParserIdx in nonParserStrings:
    del boshFunctions[nonParserIdx - indexShifter]
    indexShifter += 1

print(boshFunctions)
