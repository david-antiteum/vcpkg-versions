import argparse
from vcpckversions import PortsRepo, Port, PortsDB

if __name__ == "__main__":
	parser = argparse.ArgumentParser( description='Query ports.' )
	parser.add_argument( "--pkg", dest="pkg", help="Package to query with an optional version. Example: zlib or zlib/1.2.11-1")
	parser.add_argument( "--db", dest="db", help="SQLite file with ports information")
	parser.add_argument( "--like", dest="like", action='store_true', help="Look for packages with a similar name. Version is not used.")

	args = parser.parse_args()
	if args.db and args.pkg:
		db = PortsDB( None )
		db.connect( args.db )
		pkgFolderAndVersion = args.pkg.split( "/" )
		if len( pkgFolderAndVersion ) == 2:
			pkgFolder = pkgFolderAndVersion[0]
			pkgVersion = pkgFolderAndVersion[1]
		elif len( pkgFolderAndVersion ) == 1:
			pkgFolder = pkgFolderAndVersion[0]
			pkgVersion = ""
		else:
			print( "Wrong package parameter" )
			parser.print_help()
			exit()

		if pkgFolder:
			if args.like:
				packagesLike = db.packagesLike( pkgFolder )
				if len( packagesLike ) == 1:
					for v in db.versions( packagesLike[0] ):
						port = db.port( packagesLike[0], v )
						print( port )
				else:
					print( packagesLike )
			elif pkgVersion:
				port = db.port( pkgFolder, pkgVersion )
				print( port )
			else:
				for v in db.versions( pkgFolder ):
					port = db.port( pkgFolder, v, False )
					print( port )
	else:
		parser.print_help()
