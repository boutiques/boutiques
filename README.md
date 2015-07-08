# Boutiques schema
JSON schema for Boutiques application descriptors.

## Mandatory properties
* **`name`:** name of the tool described.
* **`description`:** description of the tool described.
* **`command-line`:** string representing the command line. May contain command line "keys" that will be substituted by the input/output values and flags. Example: "my_tool [PARAM1] [IN_FILE] [PARAM2] [OUT_FILE]"
* **`schema-version`:** version of the Boutiques schema used.
* **`inputs`:** an array of inputs.
  Input properties:
  * **`name`**
  * **`type`**
  * **`description`**
  * `command-line-key`
  * `cardinality`
  * `optional`
  * `command-line-flag`
* `outputs`: an array of outputs.
  Output properties: 
  * **`name`**, **`type`**, **`description`**: see description of input properties.
  * **`value-template`**
  * `command-line-key`, `cardinality`, `optional`, `command-line-flag`: see description of input properties.
* `tool-version`:
* `docker-image`:
* `docker-index`:
  