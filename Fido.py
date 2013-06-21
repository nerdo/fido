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
					if isInProject == False:
						isInProject = True
						foundInPath = aProjectPath

					if 'fido' not in folder: continue
					fido = folder['fido']

					# build the command
					commands += FidoUtils.__build_commands(fido, aProjectPath, getAll = False if len(commands) else True)

		if 'fido' in project:
			fido = project['fido']
			commands += FidoUtils.__build_commands(
				fido, foundInPath, getAll = isInProject and not len(commands), projectBasePath = projectBasePath, fileName = savedFileName
			)

		return commands

	def __build_commands(fido, path, getAll = False, fileName = None, projectBasePath = None):
		commands = []
		# build the command
		command = None
		if isinstance(fido, str):
			command = fido
			alwaysRun = True if getAll else False
		elif isinstance(fido, list) and getAll:
			for f in fido:
				commands += FidoUtils.__build_commands(f, path, getAll = getAll, fileName = fileName, projectBasePath = projectBasePath)
		elif (isinstance(fido, dict) and 'command' in fido):
			if 'path' in fido:
				if fileName != None:
					# see if the file is within the path
					aProjectPath = fido['path']
					if os.path.isabs(aProjectPath) != True and projectBasePath != None:
						aProjectPath = os.path.join(projectBasePath, aProjectPath)
					if fido.get('follow_symlinks', False):
						aProjectPath = os.path.realpath(aProjectPath)
						testFileName = os.path.realpath(fileName)
					else:
						testFileName = fileName
					if os.path.commonprefix([aProjectPath, testFileName]) == aProjectPath:
						command = fido['command']
						alwaysRun = getAll
			else:
				command = fido['command']
				alwaysRun = getAll

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

		# get commands
		commands = FidoUtils.get_commands(project, projectBasePath, savedFileName)

		for command in commands:
			# run it
			thread = FidoCommandThread(command)
			thread.start()

class FidoCommandThread(threading.Thread):
	def __init__(self, command):
		self.__command = command
		threading.Thread.__init__(self)

	def run(self):
		try:
			os.chdir(self.__command.get('path'))
			print(
				'fido$ ' + str(self.__command.get('command')) + '\n' +
				subprocess.check_output(self.__command.get('command'), shell=True, stderr=subprocess.STDOUT).decode('utf-8')
			)
		except CalledProcessError as error:
			print('fido$ ' + str(self.__command.get('command')) + '\n' + error.output.decode('utf-8'))
