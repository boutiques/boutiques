# Boutiques schema

The JSON schema for Boutiques tool descriptors.

## Schema properties

Mandatory properties are in bold.

* **`name`:** name of the tool described.
* **`description`:** description of the tool described.
* **`command-line`:** string representing the command line. May contain command line "keys" that will be substituted by the input/output values and flags. Example: 
```
my_tool [PARAM1] [IN_FILE] [PARAM2] [OUT_FILE]
```
* **`schema-version`:** version of the Boutiques schema used.
* **`inputs`:** an array of objects with the following properties:
  * **`name`:** name of the input.
  * **`type`:** type of the input.
  * **`description`:** description of the input.
  * `command-line-key`: a string included in `command-line`, that will be substituted with the input `command-line-flag` and value at runtime. Inputs may have no `command-line-key`, for instance when the tool assumes that a file not mentioned on the command line is present.
  * `cardinality`: "Single" if the input can take only 1 value, otherwise "Multiple". Defaults to Single. 
  * `optional`
  * `command-line-flag`
* `outputs`: an array of objects with the following properties:
  * **`name`**, **`type`**, **`description`**: see description of input properties.
  * **`value-template`**
  * `command-line-key`, `cardinality`, `optional`, `command-line-flag`: see description of input properties.
* `tool-version`:
* `docker-image`:
* `docker-index`:
  