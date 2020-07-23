
# Tool Schema

```
```


| Abstract | Extensible | Status | Identifiable | Custom Properties | Additional Properties | Defined In |
|----------|------------|--------|--------------|-------------------|-----------------------|------------|
| Can be instantiated | No | Experimental | No | Forbidden | Forbidden |  |

# Tool Properties

| Property | Type | Required | Defined by |
|----------|------|----------|------------|
| [author](#author) | `string` | Optional | Tool (this schema) |
| [command-line](#command-line) | `string` | **Required** | Tool (this schema) |
| [container-image](#container-image) | `object` | Optional | Tool (this schema) |
| [custom](#custom) | `object` | Optional | Tool (this schema) |
| [deprecated-by-doi](#deprecated-by-doi) | complex | Optional | Tool (this schema) |
| [description](#description) | `string` | **Required** | Tool (this schema) |
| [descriptor-url](#descriptor-url) | `string` | Optional | Tool (this schema) |
| [doi](#doi) | `string` | Optional | Tool (this schema) |
| [environment-variables](#environment-variables) | `object[]` | Optional | Tool (this schema) |
| [error-codes](#error-codes) | `object[]` | Optional | Tool (this schema) |
| [groups](#groups) | `object[]` | Optional | Tool (this schema) |
| [inputs](#inputs) | `object[]` | **Required** | Tool (this schema) |
| [invocation-schema](#invocation-schema) | `object` | Optional | Tool (this schema) |
| [name](#name) | `string` | **Required** | Tool (this schema) |
| [online-platform-urls](#online-platform-urls) | `string[]` | Optional | Tool (this schema) |
| [output-files](#output-files) | `object[]` | Optional | Tool (this schema) |
| [schema-version](#schema-version) | `enum` | **Required** | Tool (this schema) |
| [shell](#shell) | `string` | Optional | Tool (this schema) |
| [suggested-resources](#suggested-resources) | `object` | Optional | Tool (this schema) |
| [tags](#tags) | `object` | Optional | Tool (this schema) |
| [tests](#tests) | `object[]` | Optional | Tool (this schema) |
| [tool-doi](#tool-doi) | `string` | Optional | Tool (this schema) |
| [tool-version](#tool-version) | `string` | **Required** | Tool (this schema) |
| [url](#url) | `string` | Optional | Tool (this schema) |

## author

Tool author name(s).

`author`
* is optional
* type: `string`
* defined in this schema

### author Type


`string`
* minimum length: 1 characters





## command-line

A string that describes the tool command line, where input and output values are identified by "keys". At runtime, command-line keys are substituted with flags and values.

`command-line`
* is **required**
* type: `string`
* defined in this schema

### command-line Type


`string`
* minimum length: 1 characters





## container-image


`container-image`
* is optional
* type: `object`
* defined in this schema

### container-image Type


`object` with following properties:


| Property | Type | Required |
|----------|------|----------|






## custom


`custom`
* is optional
* type: `object`
* defined in this schema

### custom Type


`object` with following properties:


| Property | Type | Required |
|----------|------|----------|






## deprecated-by-doi

doi of the tool that deprecates the current one. May be set to 'true' if the current tool is deprecated but no specific tool deprecates it.

`deprecated-by-doi`
* is optional
* type: complex
* defined in this schema

### deprecated-by-doi Type

Unknown type `string,boolean`.

```json
{
  "id": "http://github.com/boutiques/boutiques-schema/deprecated-by-doi",
  "minLength": 1,
  "description": "doi of the tool that deprecates the current one. May be set to 'true' if the current tool is deprecated but no specific tool deprecates it.",
  "type": [
    "string",
    "boolean"
  ],
  "simpletype": "complex"
}
```





## description

Tool description.

`description`
* is **required**
* type: `string`
* defined in this schema

### description Type


`string`
* minimum length: 1 characters





## descriptor-url

Link to the descriptor itself (e.g. the GitHub repo where it is hosted).

`descriptor-url`
* is optional
* type: `string`
* defined in this schema

### descriptor-url Type


`string`
* minimum length: 1 characters





## doi

DOI of the descriptor (not of the tool itself).

`doi`
* is optional
* type: `string`
* defined in this schema

### doi Type


`string`
* minimum length: 1 characters





## environment-variables

An array of key-value pairs specifying environment variable names and their values to be used in the execution environment.

`environment-variables`
* is optional
* type: `object[]`
* at least `1` items in the array
* defined in this schema

### environment-variables Type


Array type: `object[]`

All items must be of the type:
`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `description`| string | Optional |
| `name`| string | **Required** |
| `value`| string | **Required** |



#### description

Description of the environment variable.

`description`
* is optional
* type: `string`

##### description Type


`string`








#### name

The environment variable name (identifier) containing only alphanumeric characters and underscores. Example: "PROGRAM_PATH".

`name`
* is **required**
* type: `string`

##### name Type


`string`
* minimum length: 1 characters

All instances must conform to this regular expression 
(test examples [here](https://regexr.com/?expression=%5E%5Ba-z%2CA-Z%5D%5B0-9%2C_%2Ca-z%2CA-Z%5D*%24)):
```regex
^[a-z,A-Z][0-9,_,a-z,A-Z]*$
```








#### value

The value of the environment variable.

`value`
* is **required**
* type: `string`

##### value Type


`string`














## error-codes

An array of key-value pairs specifying exit codes and their description. Can be used for tools to specify the meaning of particular exit codes. Exit code 0 is assumed to indicate a successful execution.

`error-codes`
* is optional
* type: `object[]`
* at least `1` items in the array
* defined in this schema

### error-codes Type


Array type: `object[]`

All items must be of the type:
`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `code`| integer | **Required** |
| `description`| string | **Required** |



#### code

Value of the exit code

`code`
* is **required**
* type: `integer`

##### code Type


`integer`








#### description

Description of the error code.

`description`
* is **required**
* type: `string`

##### description Type


`string`














## groups

Sets of identifiers of inputs, each specifying an input group.

`groups`
* is optional
* type: `object[]`
* at least `1` items in the array
* defined in this schema

### groups Type


Array type: `object[]`

All items must be of the type:
`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `all-or-none`| boolean | Optional |
| `description`| string | Optional |
| `id`| string | **Required** |
| `members`| array | **Required** |
| `mutually-exclusive`| boolean | Optional |
| `name`| string | **Required** |
| `one-is-required`| boolean | Optional |



#### all-or-none

True if members of the group need to be toggled together

`all-or-none`
* is optional
* type: `boolean`

##### all-or-none Type


`boolean`







#### description

Description of the input group.

`description`
* is optional
* type: `string`

##### description Type


`string`








#### id

A short, unique, informative identifier containing only alphanumeric characters and underscores. Typically used to generate variable names. Example: "outfile_group".

`id`
* is **required**
* type: `string`

##### id Type


`string`
* minimum length: 1 characters

All instances must conform to this regular expression 
(test examples [here](https://regexr.com/?expression=%5E%5B0-9%2C_%2Ca-z%2CA-Z%5D*%24)):
```regex
^[0-9,_,a-z,A-Z]*$
```








#### members

IDs of the inputs belonging to this group.

`members`
* is **required**
* type: `string[]`


##### members Type


Array type: `string[]`

All items must be of the type:
`string`
* minimum length: 1 characters

All instances must conform to this regular expression 
(test examples [here](https://regexr.com/?expression=%5E%5B0-9%2C_%2Ca-z%2CA-Z%5D*%24)):
```regex
^[0-9,_,a-z,A-Z]*$
```











#### mutually-exclusive

True if only one input in the group may be active at runtime.

`mutually-exclusive`
* is optional
* type: `boolean`

##### mutually-exclusive Type


`boolean`







#### name

A human-readable name for the input group.

`name`
* is **required**
* type: `string`

##### name Type


`string`
* minimum length: 1 characters







#### one-is-required

True if at least one of the inputs in the group must be active at runtime.

`one-is-required`
* is optional
* type: `boolean`

##### one-is-required Type


`boolean`












## inputs


`inputs`
* is **required**
* type: `object[]`
* at least `1` items in the array
* defined in this schema

### inputs Type


Array type: `object[]`

All items must be of the type:
`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `command-line-flag`| string | Optional |
| `command-line-flag-separator`| string | Optional |
| `default-value`|  | Optional |
| `description`| string | Optional |
| `disables-inputs`| array | Optional |
| `exclusive-maximum`| boolean | Optional |
| `exclusive-minimum`| boolean | Optional |
| `id`| string | **Required** |
| `integer`| boolean | Optional |
| `list`| boolean | Optional |
| `list-separator`| string | Optional |
| `max-list-entries`| number | Optional |
| `maximum`| number | Optional |
| `min-list-entries`| number | Optional |
| `minimum`| number | Optional |
| `name`| string | **Required** |
| `optional`| boolean | Optional |
| `requires-inputs`| array | Optional |
| `type`| string | **Required** |
| `uses-absolute-path`| boolean | Optional |
| `value-choices`| array | Optional |
| `value-disables`| object | Optional |
| `value-key`| string | Optional |
| `value-requires`| object | Optional |



#### command-line-flag

Option flag of the input, involved in the value-key substitution. Inputs of type "Flag" have to have a command-line flag. Examples: -v, --force.

`command-line-flag`
* is optional
* type: `string`

##### command-line-flag Type


`string`








#### command-line-flag-separator

Separator used between flags and their arguments. Defaults to a single space.

`command-line-flag-separator`
* is optional
* type: `string`

##### command-line-flag-separator Type


`string`








#### default-value

Default value of the input. The default value is set when no value is specified, even when the input is optional. If the desired behavior is to omit the input from the command line when no value is specified, then no default value should be used. In this case, the tool might still use a default value internally, but this will remain undocumented in the Boutiques interface.

`default-value`
* is optional
* type: complex

##### default-value Type

Unknown type ``.

```json
{
  "id": "http://github.com/boutiques/boutiques-schema/input/default-value",
  "description": "Default value of the input. The default value is set when no value is specified, even when the input is optional. If the desired behavior is to omit the input from the command line when no value is specified, then no default value should be used. In this case, the tool might still use a default value internally, but this will remain undocumented in the Boutiques interface.",
  "simpletype": "complex"
}
```







#### description

Input description.

`description`
* is optional
* type: `string`

##### description Type


`string`








#### disables-inputs

Ids of the inputs that are disabled when this input is active.

`disables-inputs`
* is optional
* type: `string[]`


##### disables-inputs Type


Array type: `string[]`

All items must be of the type:
`string`











#### exclusive-maximum

Specify whether the maximum is exclusive or not. May only be used with Number type inputs.

`exclusive-maximum`
* is optional
* type: `boolean`

##### exclusive-maximum Type


`boolean`







#### exclusive-minimum

Specify whether the minimum is exclusive or not. May only be used with Number type inputs.

`exclusive-minimum`
* is optional
* type: `boolean`

##### exclusive-minimum Type


`boolean`







#### id

A short, unique, informative identifier containing only alphanumeric characters and underscores. Typically used to generate variable names. Example: "data_file".

`id`
* is **required**
* type: `string`

##### id Type


`string`
* minimum length: 1 characters

All instances must conform to this regular expression 
(test examples [here](https://regexr.com/?expression=%5E%5B0-9%2C_%2Ca-z%2CA-Z%5D*%24)):
```regex
^[0-9,_,a-z,A-Z]*$
```








#### integer

Specify whether the input should be an integer. May only be used with Number type inputs.

`integer`
* is optional
* type: `boolean`

##### integer Type


`boolean`







#### list

True if input is a list of value. An input of type "Flag" cannot be a list.

`list`
* is optional
* type: `boolean`

##### list Type


`boolean`







#### list-separator

Separator used between list items. Defaults to a single space.

`list-separator`
* is optional
* type: `string`

##### list-separator Type


`string`








#### max-list-entries

Specify the maximum number of entries in the list. May only be used with List type inputs.

`max-list-entries`
* is optional
* type: `number`

##### max-list-entries Type


`number`








#### maximum

Specify the maximum value of the input (inclusive). May only be used with Number type inputs.

`maximum`
* is optional
* type: `number`

##### maximum Type


`number`








#### min-list-entries

Specify the minimum number of entries in the list. May only be used with List type inputs.

`min-list-entries`
* is optional
* type: `number`

##### min-list-entries Type


`number`








#### minimum

Specify the minimum value of the input (inclusive). May only be used with Number type inputs.

`minimum`
* is optional
* type: `number`

##### minimum Type


`number`








#### name

A human-readable input name. Example: 'Data file'.

`name`
* is **required**
* type: `string`

##### name Type


`string`
* minimum length: 1 characters







#### optional

True if input is optional.

`optional`
* is optional
* type: `boolean`

##### optional Type


`boolean`







#### requires-inputs

Ids of the inputs or ids of groups whose members must be active for this input to be available.

`requires-inputs`
* is optional
* type: `string[]`


##### requires-inputs Type


Array type: `string[]`

All items must be of the type:
`string`











#### type

Input type.

`type`
* is **required**
* type: `enum`

The value of this property **must** be equal to one of the [known values below](#inputs-known-values).

##### type Known Values
| Value | Description |
|-------|-------------|
| `String` |  |
| `File` |  |
| `Flag` |  |
| `Number` |  |






#### uses-absolute-path

Specifies that this input must be given as an absolute path. Only specifiable for File type inputs.

`uses-absolute-path`
* is optional
* type: `boolean`

##### uses-absolute-path Type


`boolean`







#### value-choices

Permitted choices for input value. May not be used with the Flag type.

`value-choices`
* is optional
* type: `array`


##### value-choices Type


Array type: `array`

All items must be of the type:
Unknown type ``.

```json
{
  "id": "http://github.com/boutiques/boutiques-schema/input/value-choices",
  "description": "Permitted choices for input value. May not be used with the Flag type.",
  "type": "array",
  "items": {
    "oneOf": [
      {
        "type": "string"
      },
      {
        "type": "number"
      }
    ],
    "simpletype": "complex"
  },
  "simpletype": "`array`"
}
```










#### value-disables

Ids of the inputs that are disabled when the corresponding value choice is selected.

`value-disables`
* is optional
* type: `object`

##### value-disables Type

Unknown type `object`.

```json
{
  "id": "http://github.com/boutiques/boutiques-schema/input/value-disables",
  "description": "Ids of the inputs that are disabled when the corresponding value choice is selected.",
  "type": "object",
  "properties": {},
  "additionalProperties": true,
  "simpletype": "`object`"
}
```







#### value-key

A string contained in command-line, substituted by the input value and/or flag at runtime.

`value-key`
* is optional
* type: `string`

##### value-key Type


`string`








#### value-requires

Ids of the inputs that are required when the corresponding value choice is selected.

`value-requires`
* is optional
* type: `object`

##### value-requires Type

Unknown type `object`.

```json
{
  "id": "http://github.com/boutiques/boutiques-schema/input/value-requires",
  "description": "Ids of the inputs that are required when the corresponding value choice is selected.",
  "type": "object",
  "properties": {},
  "additionalProperties": true,
  "simpletype": "`object`"
}
```












## invocation-schema


`invocation-schema`
* is optional
* type: `object`
* defined in this schema

### invocation-schema Type


`object` with following properties:


| Property | Type | Required |
|----------|------|----------|






## name

Tool name.

`name`
* is **required**
* type: `string`
* defined in this schema

### name Type


`string`
* minimum length: 1 characters





## online-platform-urls

Online platform URLs from which the tool can be executed.

`online-platform-urls`
* is optional
* type: `string[]`

* defined in this schema

### online-platform-urls Type


Array type: `string[]`

All items must be of the type:
`string`


All instances must conform to this regular expression 
(test examples [here](https://regexr.com/?expression=%5Ehttps%3F%3A%2F%2F)):
```regex
^https?://
```









## output-files


`output-files`
* is optional
* type: `object[]`
* at least `1` items in the array
* defined in this schema

### output-files Type


Array type: `object[]`

All items must be of the type:
`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `command-line-flag`| string | Optional |
| `command-line-flag-separator`| string | Optional |
| `conditional-path-template`| array | Optional |
| `description`| string | Optional |
| `file-template`| array | Optional |
| `id`| string | **Required** |
| `list`| boolean | Optional |
| `name`| string | **Required** |
| `optional`| boolean | Optional |
| `path-template`| string | Optional |
| `path-template-stripped-extensions`| array | Optional |
| `uses-absolute-path`| boolean | Optional |
| `value-key`| string | Optional |



#### command-line-flag

Option flag of the output, involved in the value-key substitution. Examples: -o, --output

`command-line-flag`
* is optional
* type: `string`

##### command-line-flag Type


`string`








#### command-line-flag-separator

Separator used between flags and their arguments. Defaults to a single space.

`command-line-flag-separator`
* is optional
* type: `string`

##### command-line-flag-separator Type


`string`








#### conditional-path-template

List of objects containing boolean statement (Limited python syntax: ==, !=, <, >, <=, >=, and, or) and output file paths relative to the execution directory, assign path of first true boolean statement. May contain input value keys, "default" object required if "optional" set to True . Example list: "[{"[PARAM1] > 8": "outputs/[INPUT1].txt"}, {"default": "outputs/default.txt"}]".

`conditional-path-template`
* is optional
* type: `object[]`


##### conditional-path-template Type


Array type: `object[]`

All items must be of the type:
`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `propertyNames`|  | Optional |



#### propertyNames

undefined

`propertyNames`
* is optional
* type: complex

##### propertyNames Type

Unknown type ``.

```json
{
  "pattern": "^[A-Za-z0-9_><=!)( ]*$",
  "simpletype": "complex"
}
```














#### description

Output description.

`description`
* is optional
* type: `string`

##### description Type


`string`








#### file-template

An array of strings that may contain value keys. Each item will be a line in the configuration file.

`file-template`
* is optional
* type: `string[]`
* at least `1` items in the array


##### file-template Type


Array type: `string[]`

All items must be of the type:
`string`











#### id

A short, unique, informative identifier containing only alphanumeric characters and underscores. Typically used to generate variable names. Example: "data_file"

`id`
* is **required**
* type: `string`

##### id Type


`string`
* minimum length: 1 characters

All instances must conform to this regular expression 
(test examples [here](https://regexr.com/?expression=%5E%5B0-9%2C_%2Ca-z%2CA-Z%5D*%24)):
```regex
^[0-9,_,a-z,A-Z]*$
```








#### list

True if output is a list of value.

`list`
* is optional
* type: `boolean`

##### list Type


`boolean`







#### name

A human-readable output name. Example: 'Data file'

`name`
* is **required**
* type: `string`

##### name Type


`string`
* minimum length: 1 characters







#### optional

True if output may not be produced by the tool.

`optional`
* is optional
* type: `boolean`

##### optional Type


`boolean`







#### path-template

Describes the output file path relatively to the execution directory. May contain input value keys and wildcards. Example: "results/[INPUT1]_brain*.mnc".

`path-template`
* is optional
* type: `string`

##### path-template Type


`string`
* minimum length: 1 characters







#### path-template-stripped-extensions

List of file extensions that will be stripped from the input values before being substituted in the path template. Example: [".nii",".nii.gz"].

`path-template-stripped-extensions`
* is optional
* type: `string[]`


##### path-template-stripped-extensions Type


Array type: `string[]`

All items must be of the type:
`string`











#### uses-absolute-path

Specifies that this output filepath will be given as an absolute path.

`uses-absolute-path`
* is optional
* type: `boolean`

##### uses-absolute-path Type


`boolean`







#### value-key

A string contained in command-line, substituted by the output value and/or flag at runtime.

`value-key`
* is optional
* type: `string`

##### value-key Type


`string`














## schema-version

Version of the schema used.

`schema-version`
* is **required**
* type: `enum`
* defined in this schema

The value of this property **must** be equal to one of the [known values below](#schema-version-known-values).

### schema-version Known Values
| Value | Description |
|-------|-------------|
| `0.5` |  |




## shell

Absolute path of the shell interpreter to use in the container (defaults to /bin/sh).

`shell`
* is optional
* type: `string`
* defined in this schema

### shell Type


`string`
* minimum length: 1 characters





## suggested-resources


`suggested-resources`
* is optional
* type: `object`
* defined in this schema

### suggested-resources Type


`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `cpu-cores`| integer | Optional |
| `disk-space`| number | Optional |
| `nodes`| integer | Optional |
| `ram`| number | Optional |
| `walltime-estimate`| number | Optional |



#### cpu-cores

The requested number of cpu cores to run the described application

`cpu-cores`
* is optional
* type: `integer`

##### cpu-cores Type


`integer`
* minimum value: `1`








#### disk-space

The requested number of GB of storage to run the described application

`disk-space`
* is optional
* type: `number`

##### disk-space Type


`number`
* minimum value: `0`








#### nodes

The requested number of nodes to spread the described application across

`nodes`
* is optional
* type: `integer`

##### nodes Type


`integer`
* minimum value: `1`








#### ram

The requested number of GB RAM to run the described application

`ram`
* is optional
* type: `number`

##### ram Type


`number`
* minimum value: `0`








#### walltime-estimate

Estimated wall time of a task in seconds.

`walltime-estimate`
* is optional
* type: `number`

##### walltime-estimate Type


`number`
* minimum value: `0`











## tags

A set of key-value pairs specifying tags describing the pipeline. The tag names are open, they might be more constrained in the future.

`tags`
* is optional
* type: `object`
* defined in this schema

### tags Type


`object` with following properties:


| Property | Type | Required |
|----------|------|----------|






## tests


`tests`
* is optional
* type: `object[]`
* at least `1` items in the array
* defined in this schema

### tests Type


Array type: `object[]`

All items must be of the type:
`object` with following properties:


| Property | Type | Required |
|----------|------|----------|
| `assertions`| object | **Required** |
| `invocation`| object | **Required** |
| `name`| string | **Required** |



#### assertions

undefined

`assertions`
* is **required**
* type: `object`

##### assertions Type


**Any** following *options* needs to be fulfilled.


#### Option 1



#### Option 2









#### invocation

undefined

`invocation`
* is **required**
* type: `object`

##### invocation Type

Unknown type `object`.

```json
{
  "id": "http://github.com/boutiques/boutiques-schema/tests/test-case/invocation",
  "type": "object",
  "simpletype": "`object`"
}
```







#### name

Name of the test-case

`name`
* is **required**
* type: `string`

##### name Type


`string`
* minimum length: 1 characters













## tool-doi

DOI of the tool (not of the descriptor).

`tool-doi`
* is optional
* type: `string`
* defined in this schema

### tool-doi Type


`string`
* minimum length: 1 characters





## tool-version

Tool version.

`tool-version`
* is **required**
* type: `string`
* defined in this schema

### tool-version Type


`string`
* minimum length: 1 characters





## url

Tool URL.

`url`
* is optional
* type: `string`
* defined in this schema

### url Type


`string`
* minimum length: 1 characters




