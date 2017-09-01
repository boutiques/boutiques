# BIDS apps in Boutiques

To integrate a [BIDS
app](http://bids-apps.neuroimaging.io) in Boutiques, import it with `bosh-import`:

```bosh-import <bids_dir> <output_file.json>```.

The resulting Boutiques descriptor will contain only the inputs that
are common to all BIDS apps, that is, `BIDS directory`, `output
directory`, `analysis level` and `participant label`. To make your
Boutiques descriptor complete, add a JSON object to the `inputs` array
for each additional input in your app. Refer to the [Getting Started
Guide](https://github.com/boutiques/boutiques/blob/master/examples/Getting%20Started%20with%20Boutiques.ipynb)
for more information.

Edit the `value-choices` property of input `analysis_level` to remove
the analysis levels that are not supported by the app. For instance,
if the app supports only participant analyses, replace:
```"value-choices" : [ "participant", "group", "session" ]```
by:
```"value-choices" : [ "participant" ]```.

## Examples

The following BIDS apps are integrated in Boutiques:

* [example](https://github.com/BIDS-Apps/example)
* [ndmg](https://github.com/BIDS-Apps/ndmg)

## Next steps

You can then use your BIDS app in the tools that support
   Boutiques:
* [CBRAIN](https://github.com/aces/cbrain)
* [clowdr](https://github.com/clowdcontrol/clowder)
* [sim](https://github.com/big-data-lab-team/sim)
* [VIP](http://github.com/virtual-imaging-platform)