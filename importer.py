import os
import argparse
from pathlib import Path
from vcpckversions import PortsRepo, Port, PortsDB

# Reads a port file
def readPort( controlFilePath ):
	port = Port()
	port.folder = os.path.basename( os.path.dirname( controlFilePath ) )
	for line in open( controlFilePath, 'r' ).readlines():
		values = line.strip().split( ":" )
		if len(values) > 1:
			if values[0].startswith( 'Source' ):
				port.name = values[1].strip()
			elif values[0].startswith( 'Version' ):
				port.version = values[1].strip()
			elif values[0].startswith( 'Description' ):
				port.description = values[1].strip()
			elif values[0].startswith( 'Build-Depends' ):
				dependencies = set()
				for depName in values[1].strip().split( ',' ):
					if depName:
						dependencies.add( depName.strip().split()[0] )
				port.dependenciesNames |= dependencies

	return port

# Reads all the port at a commit
def readPorts( db, folder, commit ):
	pathlist = Path( os.path.join( folder, "ports" ) ).glob('**/CONTROL')
	for path in pathlist:
		port = readPort( str( path ) )
		db.add( port, commit )

# Generates a SQLite database with all the ports in vcpkg repository
if __name__ == "__main__":
	parser = argparse.ArgumentParser( description='Build the port versions database.' )
	parser.add_argument( "--repository", dest="repository", help="folder with a vcpkg cloned repository at master")
	parser.add_argument( "--db", dest="db", help="SQLite file to generate")

	args = parser.parse_args()
	if args.repository and args.db:
		repo = PortsRepo( args.repository )
		db = PortsDB( repo )

		repo.readHashes()
		for h in repo.hashes:
			if repo.checkout( h ):
				readPorts( db, args.repository, h )
			else:
				break
		db.buildDependencies()
		db.store( args.db )
	else:
		parser.print_help()
