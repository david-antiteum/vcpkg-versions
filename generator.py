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

if __name__ == "__main__":
	parser = argparse.ArgumentParser( description='Generate ports folder for a package.' )
	parser.add_argument( "--pkg", dest="pkg", help="Package to read, requires a version.")
	parser.add_argument( "--pkg-version", dest="pkgVersion", help="Package version to read")
	parser.add_argument( "--db", dest="db", help="SQLite file with ports information")
	parser.add_argument( "--destination", dest="destination", help="Destination ports folder")
	parser.add_argument( "--repository", dest="repository", help="folder with a vcpkg cloned repository at master")

	args = parser.parse_args()
	if args.db and args.pkg and args.repository:
		repository = PortsRepo( args.repository )
		db = PortsDB( repository )
		db.connect( args.db )

		if args.pkgVersion:
			port = db.port( args.pkg, args.pkgVersion )
			if args.destination:
				plan = {}
				generatePlan( db, port, args.destination, plan )
				executePlan( db, args.destination, plan )
			else:
				print( port )
		else:
			for v in db.versions( args.pkg ):
				port = db.port( args.pkg, v )
				print( port )
	else:
		parser.print_help()
