# Boutiques schema

The JSON schema for Boutiques tool descriptors.

## Properties

Mandatory properties are in bold.

* **`name`:** name of the tool.
* **`description`:** description of the tool.
* **`schema-version`:** version of the Boutiques schema used.
* **`command-line`:** a string, specifying a command line template where input/output values are replaced by "keys". Example:
```
my_tool [PARAM1] [IN_FILE] [PARAM2] [OUT_FILE]
```
The format of command line keys is not specified. However, it is recommended to use easily-identifiable strings.
* **`inputs`:** an array of objects with the following properties:
  * **`name`:** name of the input.
  * **`type`:** type of the input, i.e. File, String, Flag, or Numeric.  
  * **`description`:** description of the input.
  * `command-line-key`: a string, contained in `command-line`, substituted in the `command-line` at runtime. 
  * `cardinality`: "Multiple" if multiple values may be involved in a single invocation of the tool. Defaults to Single.
  * `optional`: a boolean, true if input is optional.
  * `command-line-flag`: a string involved in the `command-line-key` substitution. Examples: ```-v```, ```--force```. 

prepended, with a space, to the input value at runtime.
* `outputs`: an array of objects with the following properties:
  * **`name`**, **`type`**, **`description`**: see description of input properties.
  * **`value-template`**
  * `command-line-key`, `cardinality`, `optional`, `command-line-flag`: see description of input properties.
* `tool-version`:
* `docker-image`:
* `docker-index`:

## Substitution

