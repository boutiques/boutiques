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
  * **`name`:** input name
  * **`type`:** input file. "File", "String", "Flag", or "Numeric". 
  * **`description`:** input description.
  * `command-line-key`: a string, contained in `command-line`, substituted at runtime. 
  * `list`: a boolean, true if input is a list of value. Defaults to false.
  * `optional`: a boolean, true if input is optional. Defaults to false.
  * `command-line-flag`: a string involved in the `command-line-key` substitution. Examples: ```-v```, ```--force```. Defaults to the empty string.
* **`outputs`**: an array of objects that represent outputs with the following properties:
  * **`name`**: output name.
  * **`description`**: output description.
  * **`path-template`**: A string that describes the output file path relatively to the execution directory. May contain input `command-line-keys` substituted at runtime. Example: ```results/[INPUT1]_brain.mnc```.
  * `command-line-key`: a string, contained in `command-line`, substituted at runtime. 
  * `list`: a boolean, true if output is a list of value. In this case, `path-template` must contain a '*' standing for "any string of characters" (as the Linux wildcard). Defaults to false.
  * `optional`: a boolean, true if output may not be produced by the tool. Defaults to false.
  * `command-line-flag`: a string involved in the `command-line-key` substitution. Examples: ```-o```, ```--output```. Defaults to the empty string.
* `tool-version`: tool version.
* `docker-image`: name of a Docker image where tool is installed and configured. Example: ```docker.io/neurodebian```.
* `docker-index`: Docker index where Docker image is available. Example: ```http://index.docker.io```.

## Command-line substitution

At runtime, inputs contain _values_:
* Inputs of type "String" may contain any string (encoding is not specified).
* Inputs of type "Numeric" must contain a string representing a number. 
* Inputs of type "File" must contain a string representing a file path (absolute or relative to the execution directory).
* Inputs of type "Flag" must contain a boolean.

The tool command line is generated as follows:

## 

