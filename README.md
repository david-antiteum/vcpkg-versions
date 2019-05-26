# vcpck-versions

Utilities to work with selected versions of port files. More information in this [blog post](http://www.antiteum.com/2019/05/vcpkg-versioning.html).

## Importer

This utility read all commits in the repository to discover the ports and all the versions. The creates a SQLite database with that information.

Example of usage:

```shell
cd $HOME
mkdir -p tmp
git clone https://github.com/microsoft/vcpkg.git
python importer.py --repository $HOME/tmp/vcpkg --db $HOME/tmp/repo.db
```

## Query

Look for packages by name.

### Examples

Look for a package using a version:

```shell
python query.py --db $HOME/tmp/repo.db --pkg boost/1.67.0
```

Look for packages with a similar name (using the LIKE operator)

```shell
python query.py --db $HOME/tmp/repo.db --pkg json --like
```

## Generator

Generates all the port files for a package and a version, including all the dependencies.

Example of usage:

```shell
cd $HOME
rm -rf vcpkg
git clone https://github.com/microsoft/vcpkg.git
rm -rf vcpkg/ports
python generator.py --repository $HOME/tmp/vcpkg --db $HOME/tmp/repo.db --destination $HOME/vcpkg/ports --pkg opencv/3.4.3-3
```
