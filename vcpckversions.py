from collections import defaultdict
import sqlite3
import subprocess

# VCPKG Repository
class PortsRepo:
	def __init__(self, folder ):
		self.hashes = {}
		self.folder = folder

	# git log --first-parent master --format=oneline
	def readHashes( self ):
		lines = subprocess.check_output(['git', 'log', '--first-parent', 'master', '--format=oneline'], cwd=self.folder)
		hashes = list(map(lambda line: line.split()[0].decode('UTF-8'), lines.splitlines() ) )
		hashes.reverse()
		self.setHashes( hashes )

	# git checkout -f
	def checkout( self, commit ):
		try:
			print("git checkout %s" % commit )
			subprocess.run(['git', 'checkout', '-f', commit], cwd=self.folder,shell=True, check=True)
		except subprocess.CalledProcessError:
			print("git checkout failed!")
			return False
		return True

	def setHashes( self, hashes ):
		pos = 0
		for h in hashes:
			self.hashes[ h ] = pos 
			pos += 1

	def hashPosition( self, hash ):
		return self.hashes[ hash ]

	def hashBeforeOrAtHash( self, hash, maxHash ):
		return self.hashPosition( hash ) <= self.hashPosition( maxHash )

# One port
class Port:
	def __init__(self):
		self.folder = ''
		self.version = ''
		self.name = ''
		self.description = ''
		self.firstCommit = ''
		self.lastCommit = ''
		self.dependenciesNames = set()
		self.dependencies = []

	def update( self, other, commit ):
		self.name = other.name
		self.description = other.description
		self.dependenciesNames = other.dependenciesNames
		self.lastCommit = commit

	def __str__(self):
		res = "{} {} {}".format( self.folder, self.version, self.lastCommit )
		for pd in self.dependencies:
			res += "\n  {} {} {}".format( pd.folder, pd.version, pd.lastCommit )
		return res

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.folder == other.folder
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

# In memory port DB (when importing)
# or using a SQLite DB when generating
class PortsDB:
	def __init__(self, repo ):
		self.ports = defaultdict(list)
		self.repo = repo
		self.db = None

	# Add a port:
	# - If a version already exists, update it with the lastest information (maybe the portfile.cmake was updated)
	# - If a version if not found, insert it
	def add( self, port, commit ):
		found = False
		for p in self.ports[ port.folder ]:
			if p.version == port.version:
				p.update( port, commit )
				found = True
		if not found:
			port.firstCommit = commit
			port.lastCommit = commit
			port.db = self
			self.ports[ port.folder ].append( port )

	# return the version of a pck (by folder name)
	def versions( self, pck ):
		versions = []
		for port in self.ports[ pck ]:
			versions.append( port.version )
		if not versions and self.db:
			cursor = self.db.cursor()
			q = 'SELECT version FROM port WHERE id=?'
			for row in cursor.execute( q, (pck,) ):
				versions.append( row[0] )

		return versions

	# return a port (by folder name) for a version
	def port( self, pck, version, findDeps = True ):
		for port in self.ports[ pck ]:
			if port.version == version:
				return port
		if self.db:
			cursor = self.db.cursor()
			q = 'SELECT id, version, name, description, first_hash, last_hash FROM port WHERE id=? AND version=?'
			for row in cursor.execute( q, ( pck, version ) ):
				port = Port()
				port.folder = row[0]
				port.version = row[1]
				port.name = row[2]
				port.description = row[3]
				port.firstCommit = row[4]
				port.lastCommit = row[5]

				if findDeps:
					qd = 'SELECT id, version, id_dep, version_dep FROM dependencies WHERE id=? AND version=?'
					for rowDeps in cursor.execute( qd, ( pck, version ) ):
						portDep = self.port( rowDeps[2], rowDeps[3], False )
						port.dependencies.append( portDep )
				return port
		
		return None

	def findNewerPortBeforeOrAtHash( self, portDepFolder, portHash ):
		res = None
		for port in self.ports[portDepFolder]:
			if self.repo.hashBeforeOrAtHash( port.firstCommit, portHash ):
				res = port
			else:
				break
		return res
	
	def buildDependencies( self ):
		if self.repo:
			for key in self.ports:
				for port in self.ports[key]:
					print( "Build dependencies {} {} ({}-{})-> {}".format( key, port.version, self.repo.hashPosition( port.firstCommit ), self.repo.hashPosition( port.lastCommit ), port.dependenciesNames ) ) 
					for dep in port.dependenciesNames:
						if dep:
							depName = dep.split( "," )[0].split()[0]
							if depName in self.ports:
								depPort = self.findNewerPortBeforeOrAtHash( depName, port.firstCommit )
								if depPort != None:
									if depPort not in port.dependencies:
#										print( "  Added {}".format( depPort.name ) ) 
										port.dependencies.append( depPort )
								else:
									print( "  Dependency not found. Package <{}>, Dependency <{}>".format( port.folder, depName ))
							else:
								print( "  Dependency not found in ports. Package <{}>, Dependency <{}>".format( port.folder, depName ))
#					print( "{} -> {} -> {}".format( port.folder, port.dependenciesNames, len( port.dependencies ) ) ) 

	def connect( self, fileName ):
		self.db = sqlite3.connect( fileName )

	# Creates and stores and in memory DB (after an import) into a new SQLite DB
	# No incremental updates are possible right now
	def store( self, fileName ):
		self.db = sqlite3.connect( fileName )
		cursor = self.db.cursor()

		q = """	CREATE TABLE IF NOT EXISTS port (
					id TEXT NOT NULL,
					version TEXT NOT NULL,
					name TEXT NOT NULL,
					description TEXT,
					first_hash TEXT NOT NULL,
					last_hash TEXT NOT NULL,
					PRIMARY KEY( id, version )
				)
			"""
		cursor.execute( q )

		q = """	CREATE TABLE IF NOT EXISTS dependencies (
					id TEXT NOT NULL,
					version TEXT NOT NULL,
					id_dep TEXT NOT NULL,
					version_dep TEXT NOT NULL
				)
			"""
		cursor.execute( q )

		q = """	CREATE INDEX idx_id_version ON dependencies (id, version)
			"""
		cursor.execute( q )

		q = """	CREATE TABLE IF NOT EXISTS commits (
					hash TEXT NOT NULL,
					pos INTEGER NOT NULL,
					PRIMARY KEY( hash )
				)
			"""
		cursor.execute( q )

		self.db.commit()

		for key in self.ports:
			for port in self.ports[key]:
				q = """ INSERT INTO port ( id, version, name, description, first_hash, last_hash )
						VALUES ( ?, ?, ?, ?, ?, ? )
					"""
				cursor.execute( q, ( port.folder, port.version, port.name, port.description, port.firstCommit, port.lastCommit ) )
				for dep in port.dependencies:
					q = """ INSERT INTO dependencies ( id, version, id_dep, version_dep )
							VALUES ( ?, ?, ?, ? )
						"""
					cursor.execute( q, ( port.folder, port.version, dep.folder, dep.version ) )
				
				self.db.commit()
		
		for commit in self.repo.hashes:
			q = """ INSERT INTO commits ( hash, pos )
					VALUES ( ?, ? )
				"""
			cursor.execute( q, ( commit, self.repo.hashes[commit] ) )
		self.db.commit()

		self.db.close()
	
	def packagesLike( self, pckLike ):
		res = []
		q = "SELECT DISTINCT id FROM port WHERE id LIKE ?"
		cursor = self.db.cursor()
		pckLikeStr = '%{}%'.format( pckLike )
		for row in cursor.execute( q, ( pckLikeStr, ) ):
			res.append( row[0] )
		return res

