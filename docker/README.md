- builder - used to build and compile everything and create debs
  - produces: python-yang-voodoo_standalone
  - produces: python-yang-voodoo_netopeer2_sysrepo_bundle

- devel - based on installing the bundle from the builder, and a git checkout and python build tools.

- release - based on installing the standalone image, no sysrepo/netopeer installed.

- debug - compile time debug options enabled

```
# Change version number inside if applicable
docker build builder

# Generate the devel image
sh build.sh

# Generate the lab image
sh build-lab.sh

# Alpine Linux minimal image
sh build-release.sh
```
