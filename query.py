import argparse
from vcpckversions import PortsRepo, Port, PortsDB

if __name__ == "__main__":
	parser = argparse.ArgumentParser( description='Query ports.' )
	parser.add_argument( "--pkg", dest="pkg", help="Package to query.")
	parser.add_argument( "--pkg-version", dest="pkgVersion", help="Package version to read")
	parser.add_argument( "--db", dest="db", help="SQLite file with ports information")
	parser.add_argument( "--like", dest="like", action='store_true', help="Like search")

	args = parser.parse_args()
	if args.db and args.pkg:
		db = PortsDB( None )
		db.connect( args.db )

		if args.like:
			packagesLike = db.packagesLike( args.pkg )
			if len( packagesLike ) == 1:
				for v in db.versions( packagesLike[0] ):
					port = db.port( packagesLike[0], v )
					print( port )
			else:
				print( packagesLike )
		elif args.pkgVersion:
			port = db.port( args.pkg, args.pkgVersion )
			print( port )
		else:
			for v in db.versions( args.pkg ):
				port = db.port( args.pkg, v, False )
				print( port )
	else:
		parser.print_help()
