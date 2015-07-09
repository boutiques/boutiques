# Boutiques schema

The JSON schema for Boutiques tool descriptors.

## Properties

Mandatory properties are in bold.

* **`name`:** name of the tool.
* **`description`:** description of the tool.
* **`schema-version`:** version of the schema used.
* **`command-line`:** a string that describes the tool command line, where input and output values are identified by "keys". At runtime, command-line keys are substituted with flags and values (see details in next Section). Example:
```
my_tool [PARAM1] [IN_FILE] [PARAM2] [OUT_FILE]
```
The format of command line keys is not specified. However, it is recommended to use easily-identifiable strings.
* **`inputs`:** an array of objects that represent inputs with the following properties:
  * **`name`:** name of the input.
  * **`type`:** type of the input. May be File, String, Flag, or Numeric.  
  * **`description`:** description of the input.
  * `command-line-key`: a string, contained in `command-line`, substituted at runtime. 
  * `list`: a boolean, true if the input is a list of value. Defaults to false.
  * `optional`: a boolean, true if input is optional. Defaults to false.
  * `command-line-flag`: a string involved in the `command-line-key` substitution. Examples: ```-v```, ```--force```. 
* `outputs`: an array of objects that represent outputs with the following properties:
  * **`name`**: name of the output.
  * **`description`**: description of the output.
  * **`path-template`**: A string that describes the output file path relatively to the execution directory. May contain input `command-line-keys` that will be substituted at runtime. Example: ```[INPUT1]_brain.mnc```.
  * `command-line-key`: a string, contained in `command-line`, substituted at runtime. 
  * `list`: a boolean, true if the output is a list of value. In this case, `path-template` must contain a '*' standing for "any string of characters" (as the Linux wildcard).
  * `optional`: a boolean, true if output may not be produced by the tool.
  * `command-line-flag`: same description as in input properties.
* `tool-version`: the version of the tool described.
* `docker-image`: the name of a Docker image where the tool is installed and configured. Example: ```docker.io/neurodebian```.
* `docker-index`: the Docker index where the Docker image is available. Example: ```http://index.docker.io```.

## Substitution



## 

