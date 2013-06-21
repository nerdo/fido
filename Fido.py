"""
Module:      Fido
Description: A sublime plugin which runs a command when a file on the project path has been saved.
Author:      Dannel Albert <cuebix@gmail.com>
"""
import sublime, sublime_plugin, os, subprocess, threading

class FidoUtils:
	def get_commands(project, projectBasePath, savedFileName):
		commands = []
		folders = project.get('folders', [])
		isInProject = False
		foundInPath = None
		if isinstance(folders, list):
			for folder in folders:
				# see if file is in path
				if ('path' not in folder): continue

				aProjectPath = folder['path']
				if os.path.isabs(aProjectPath) != True: aProjectPath = os.path.join(projectBasePath, aProjectPath)

				if folder.get('follow_symlinks', False):
					aProjectPath = os.path.realpath(aProjectPath)
					testFileName = os.path.realpath(savedFileName)
				else:
					testFileName = savedFileName

				if os.path.commonprefix([aProjectPath, testFileName]) == aProjectPath:
					# it's in the project, look for a fido command defined for the path
					if ('fido' not in folder): continue
					fido = folder['fido']

					# build the command
					commands += FidoUtils.__build_commands(fido, aProjectPath, getAll = not isInProject)
					if isInProject == False:
						isInProject = True
						foundInPath = aProjectPath

					# if (isinstance(fido, str) or isinstance(fido, list)):
					# 	command = fido
					# 	alwaysRun = False
					# elif (isinstance(fido, dict) and 'command' in fido):
					# 	command = fido['command']
					# 	alwaysRun = fido.get('alwaysRun', False)
					# else:
					# 	continue

					# if not len(commands) or alwaysRun:
					# 	commands.append({ 'path': aProjectPath, 'command': command, 'alwaysRun': alwaysRun })

		print(len(commands), isInProject)
		if isInProject and 'fido' in project:
			fido = project['fido']
			print(len(commands))
			commands += FidoUtils.__build_commands(fido, foundInPath, getAll = False if len(commands) else True)
			# command = None
			# if (isinstance(fido, str) or isinstance(fido, list)):
			# 	command = fido
			# 	alwaysRun = False
			# elif (isinstance(fido, dict) and 'command' in fido):
			# 	command = fido['command']
			# 	alwaysRun = fido.get('alwaysRun', False)

			# if command != None:
			# 	commands.append({ 'path': aProjectPath, 'command': command, 'alwaysRun': alwaysRun })
		# elif (isinstance(folders, str)):
		# 	aProjectPath = projectBasePath
		# 	testFileName = savedFileName
		# 	print(testFileName, aProjectPath)
		# 	if (os.path.commonprefix([aProjectPath, testFileName]) == aProjectPath):
		# 		# it's in the project, look for a fido command defined for the path
		# 		commands.append({ 'path': aProjectPath, 'command': folders, 'alwaysRun': False })

		return commands

	def __build_commands(fido, path, getAll = False):
		commands = []
		# build the command
		command = None
		if isinstance(fido, str):
			command = fido
			alwaysRun = True if getAll else False
		elif isinstance(fido, list) and getAll:
			for f in fido:
				commands += FidoUtils.__build_commands(f, path, getAll)
		elif (isinstance(fido, dict) and 'command' in fido):
			command = fido['command']
			alwaysRun = fido.get('alwaysRun', False)
		if command != None and alwaysRun:
			commands.append({'path': path, 'command': command})
		return commands

class FidoEventListener(sublime_plugin.EventListener):
	def on_post_save(self, view):
		projectFileName = view.window().project_file_name()
		if projectFileName is None: return

		project = view.window().project_data().copy()

		if 'fido' in project:
			defaultFido = project['fido']
		else:
			defaultFido = None

		savedFileName = view.file_name()
		projectBasePath = os.path.dirname(projectFileName)
		thread = None

		# make sure the file is on the project path
		commands = FidoUtils.get_commands(project, projectBasePath, savedFileName)
		# commands += FidoUtils.get_commands(project.get('fido', []), projectBasePath, savedFileName)
		print(commands)
		for folder in project['folders']:
			# see if file is in path
			if ('path' not in folder): continue

			aProjectPath = folder['path']
			if (os.path.isabs(aProjectPath) != True): aProjectPath = os.path.join(projectBasePath, aProjectPath)

			if ('follow_symlinks' in folder and folder['follow_symlinks']):
				aProjectPath = os.path.realpath(aProjectPath)
				testFileName = os.path.realpath(savedFileName)
			else:
				testFileName = savedFileName

			if (os.path.commonprefix([aProjectPath, testFileName]) == aProjectPath):
				# it's in the project, look for a fido command defined for the path
				fido = None
				if ('fido' in folder):
					fido = folder['fido']
				else:
					fido = defaultFido
				if (fido is None): continue

				# build the command
				command = None
				if (isinstance(fido, str) or isinstance(fido, list)):
					command = fido
					# shell = False
				elif (isinstance(fido, dict) and 'command' in fido):
					command = fido['command']
					# shell = True if ('shell' in fido and fido['shell']) else False

				# run it
				if (command is not None):
					thread = FidoCommandThread(command)
					thread.start()
					break

class FidoCommandThread(threading.Thread):
	def __init__(self, command):
		self.__command = command
		threading.Thread.__init__(self)

	def run(self):
		print('\nfido$ ' + str(self.__command))
		try:
			print(subprocess.check_output(self.__command, shell=True, stderr=subprocess.STDOUT).decode('utf-8'))
		except CalledProcessError as error:
			print(error.output.decode('utf-8'))
