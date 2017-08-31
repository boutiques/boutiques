# BIDS apps in Boutiques

Here is how to integrate a [BIDS
app](http://bids-apps.neuroimaging.io) in Boutiques:
1. Copy `template.json`.
2. Edit the following strings identified by `@@...@@`:
   1. APP_NAME: BIDS app name.
   2. VERION: BIDS app version.
   3. GIT_REPO_URL: URL of the BIDS app Git repo.
   4. DOCKER_ENTRYPOINT: Entrypoint used in the Docker container. Example: `/run.py`.
   5. CONTAINER_IMAGE: Container image name available on DockerHub. Example: `bids/example`.
   6. ANALYSIS_TYPES: The types of analyses supported by the BIDS app. Example: "participant", "group".
3. That's it!

## Examples

The following BIDS apps were integrated in Boutiques:

* [example](https://github.com/BIDS-Apps/example)
* [ndmg](https://github.com/BIDS-Apps/ndmg)

## You can then use your BIDS app in the tools that support
   Boutiques:

* [CBRAIN](https://github.com/aces/cbrain)
* [clowdr](https://github.com/clowdcontrol/clowder)
* [sim](https://github.com/big-data-lab-team/sim)
