class: CommandLineTool
cwlVersion: v1.0
baseCommand: ["cat", "example.conf"]

requirements:
  InitialWorkDirRequirement:
    listing:
      - entryname: example.conf
        entry: |
          CONFIGVAR=$(inputs.message)

inputs:
  message: string
outputs:
  output:
    type: File
    outputBinding:
      glob: "./test_temp/example.conf"
stdout: ./test_temp/stdout.txt
