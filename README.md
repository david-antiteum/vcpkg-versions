# vcpck-versions

Utilities to work with selected version of ports files.

## Importer

This utility read all commits in the repository to discover the ports and all the versions. The creates a SQLite database with that information.

Example of usage:

```shell
cd $HOME
mkdir -p tmp
git clone https://github.com/microsoft/vcpkg.git
python importer.py --repository $HOME/tmp/vcpkg --db $HOME/tmp/repo.db
```

## Generator

Generates all the port files for a package and a version, including all the dependencies.

Example of usage:

```shell
cd $HOME
rm -rf vcpkg
git clone https://github.com/microsoft/vcpkg.git
rm -rf vcpkg/ports
python generator.py --repository $HOME/tmp/vcpkg --db $HOME/tmp/repo.db --destination $HOME/vcpkg/ports --pkg opencv --pkg-version 3.4.3-3
```
