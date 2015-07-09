# Boutiques schema

The JSON schema for Boutiques descriptors.

## Properties

Mandatory properties are in bold. Note that Boutiques descriptors may contain additional, unspecified properties providing extra information about the tool. It is strongly recommended that implementations do not critically depend on unspecified properties.

* **`name`:** tool name.
* **`description`:** tool description.
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
  * `command-line-key`: a string, contained in `command-line`, substituted by the input value and/or flag at runtime. 
  * `list`: a boolean, true if input is a list of value. Defaults to false. An input of type "Flag" may not be a list.
  * `optional`: a boolean, true if input is optional. Defaults to false.
  * `command-line-flag`: a string involved in the `command-line-key` substitution. Examples: ```-v```, ```--force```. Defaults to the empty string.
* **`output-files`**: an array of objects that represent output files with the following properties:
  * **`name`**: output name.
  * **`description`**: output description.
  * **`path-template`**: A string that describes the output file path relatively to the execution directory. May contain input `command-line-keys`. Example: ```results/[INPUT1]_brain.mnc```.
  * `command-line-key`: a string, contained in `command-line`, substituted by the output value/flag at runtime. 
  * `list`: a boolean, true if output is a list of value. In this case, `path-template` must contain a '*' standing for any string of characters (as the Linux wildcard). Defaults to false.
  * `optional`: a boolean, true if output may not be produced by the tool. Defaults to false.
  * `command-line-flag`: option flag of the output, involved in the `command-line-key` substitution. Examples: ```-o```, ```--output```. Defaults to the empty string.
* `tool-version`: tool version.
* `docker-image`: name of a Docker image where tool is installed and configured. Example: ```docker.io/neurodebian```.
* `docker-index`: Docker index where Docker image is available. Example: ```http://index.docker.io```.

## Command-line substitution

At runtime, a __value__ is assigned to each input in ```inputs```.

* Inputs of type "String" may contain any string (encoding is not specified).
* Inputs of type "Numeric" must contain a string representing a number.
* Inputs of type "File" must contain a string representing a file path (absolute or relative to the execution directory). 
* Inputs of type "Flag" must contain a boolean.

When input is a list, __value__ contains the concatenation of all strings in the list, separated by spaces. Spaces included in list elements must be escaped by '\', or the elements must be single-quoted (Linux conventions).  An input of type "Flag" may not be a list. 

The tool command line is generated as follows:

1. For each input in ```inputs```, where input has a ```command-line-key``` and input has __value__:
  * In ```command-line```, replace input ```command-line-key``` by:
         * ```command-line-flag``` if input is of type "Flag".
         * ```command-line-flag``` __value__ (space-separated) otherwise.  
  * For each output in ```output-files```
         * If ```path-template``` contains input ```command-line-key```, replace ```command-line-key``` by __value__, having previously removed the last occurrence of character '.' and subsequent characters from __value__ when input is of type "File".
2. For each output in ```output-files```, where output has a ```command-line-key```:
  * In ```command-line```, replace output ```command-line-key``` by:
         * ```command-line-flag``` ```path-template``` (space-separated). At this step, input ```command-line-key```s contained in ```path-template``` are already substituted.

## Examples (TODO)

* Inputs without command-line key.
* Outputs without command-line key.
* List outputs with a command-line key. Command-line will contain a '*'.
* List outputs without a command-line key. 
