# Generates port files for a library at a given version
# Use:
# --pkg to set the port name (as the port folder name)
# 

import argparse
import os
from pathlib import Path
from vcpckversions import PortsRepo, Port, PortsDB
import shutil
from collections import defaultdict

def generatePlan( db, port, destination, plan ):
	if not port.folder in plan:
		plan[ port.folder ] = port.lastCommit
		for dep in port.dependencies:
			generatePlan( db, dep, destination, plan )

def executePlan( db, destination, plan ):
	hashes = defaultdict(list)
	for port in plan:
		hashes[ plan[port] ].append( port )

	originPorts = os.path.join( db.repo.folder, "ports" )
	for commit in hashes:
		db.repo.checkout( commit )
		for portFolder in hashes[ commit ]:
			if os.path.exists( os.path.join( destination, portFolder ) ):
				shutil.rmtree( os.path.join( destination, portFolder ) )
			shutil.copytree( os.path.join( originPorts, portFolder ), os.path.join( destination, portFolder ) )

# Copies the selected port file (for a version, with all the dependencies) into a vcpkg local installation
#
if __name__ == "__main__":
	parser = argparse.ArgumentParser( description='Generate ports folder for a package.' )
	parser.add_argument( "--pkg", dest="pkg", help="Package to read, requires a version in the format name/version. For example zlib/1.2.11-1")
	parser.add_argument( "--db", dest="db", help="SQLite file with ports information")
	parser.add_argument( "--destination", dest="destination", help="Destination ports folder")
	parser.add_argument( "--repository", dest="repository", help="Folder with a vcpkg cloned repository at master from where we will read the port file")

	args = parser.parse_args()
	if args.db and args.pkg and args.repository and args.destination:
		pkgFolderAndVersion = args.pkg.split( "/" )
		if len( pkgFolderAndVersion ) == 2:
			pkgFolder = pkgFolderAndVersion[0]
			pkgVersion = pkgFolderAndVersion[1]

			repository = PortsRepo( args.repository )
			db = PortsDB( repository )
			db.connect( args.db )

			port = db.port( pkgFolder, pkgVersion )
			plan = {}
			generatePlan( db, port, args.destination, plan )
			if plan:
				executePlan( db, args.destination, plan )
			else:
				print( "Nothing to execute" )
		else:
			print( "Wrong package parameter" )
			parser.print_help()
	else:
		parser.print_help()
