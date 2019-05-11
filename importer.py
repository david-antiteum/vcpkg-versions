import os
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict

class Port:
	folder = ''
	name = ''
	version = ''
	description = ''
	commit = ''
	dependencies = []

class PortsDB:
	ports = defaultdict(list)

	# Add a port:
	# - If a version already exists, update it with the lastest information (maybe the portfile.cmake was updated)
	# - If a version if not found, insert it
	def add( self, port ):
		found = False
		for p in self.ports[ port.folder ]:
			if p.version == port.version:
				p = port
				found = True
		if not found:
			self.ports[ port.folder ].append( port )

	# return the version of a pck (by folder name)
	def versions( self, pck ):
		versions = []
		for port in self.ports[ pck ]:
			versions.append( port.version )
		return versions

	def buildDependencies( self, hashes ):
		pass

	# Table 
	# folder, pos, hash, name, version, description, dependencies

# git log --first-parent master --format=oneline
def getHashes( folder ):
	lines = subprocess.check_output(['git', 'log', '--first-parent', 'master', '--format=oneline'], cwd=folder)
	return list(map(lambda line: line.split()[0].decode('UTF-8'), lines.splitlines() ) ).reverse()

# git checkout -f
def checkout( folder, hash ):
	try:
		print("git checkout %s" % hash )
		subprocess.run(['git', 'checkout', '-f', hash], cwd=folder,shell=True, check=True)
	except subprocess.CalledProcessError:
		print("git checkout failed!")
		return False
	return True

def readPort( controlFilePath ):
	port = Port()
	for line in open( controlFilePath, 'r' ).readlines():
		values = line.strip().split()
		if len(values) > 1:
			if values[0].startswith( 'Source:' ):
				port.name = values[1].strip()
			elif values[0].startswith( 'Version:' ):
				port.version = values[1].strip()
			elif values[0].startswith( 'Description:' ):
				port.description = values[1].strip()
			elif values[0].startswith( 'Build-Depends:' ):
				port.dependencies = values[1].strip().split( ',' )
	return port

def readPorts( db, folder, hash ):
	pathlist = Path( os.path.join( folder, "ports" ) ).glob('**/CONTROL')
	for path in pathlist:
		port = readPort( str( path ) )
		port.folder = os.path.basename( os.path.dirname( path ) )
		port.commit = hash
#		print( "%s -> %s: %s" % ( port.folder, port.name, port.version) )
		db.add( port )

if __name__ == "__main__":
	parser = argparse.ArgumentParser( description='Build the port versions database.' )
	parser.add_argument( "--repository", dest="repository", help="folder with a vcpkg cloned repository at master")
	parser.add_argument( "--db", dest="db", help="SQLite file to update")

	args = parser.parse_args()
	if args.repository:
		db = PortsDB()

		if False:
			readPorts( db, args.repository, '00000' )
			print( db.versions( 'uriparser' ) )
		else:
			hashes = getHashes( args.repository )
			for h in hashes:
				if checkout( args.repository, h ):
					readPorts( db, args.repository, h )
				else:
					break
			db.buildDependencies( hashes )
			print( db.versions( '3fd' ) )
