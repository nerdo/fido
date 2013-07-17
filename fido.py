"""
Module:      Fido
Description: A sublime plugin which runs a command when a file on the project path has been saved.
Author:      Dannel Albert <cuebix@gmail.com>
"""
import sys, sublime, sublime_plugin, os, subprocess, threading

class FidoUtils:
	def get_commands(self, project, projectBasePath, savedFileName):
		"""
		Returns an array of commands to be run for the saved file name.
		"""
		commands = []
		folders = project.get('folders', [])
		isInProject = False
		foundInPath = None
		if isinstance(folders, list):
			for folder in folders:
				# see if file is in path
				aProjectPath = folder.get('path')
				if aProjectPath is None: continue

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

					if not hasattr(folder, 'fido'): continue
					fido = folder['fido']

					# build the command
					commands += self.__build_commands(fido, aProjectPath, getAll = False if len(commands) else True)

		fido = project.get('fido')
		if fido:
			# fido = project['fido']
			commands += self.__build_commands(
				fido, foundInPath, getAll = isInProject and not len(commands), projectBasePath = projectBasePath, fileName = savedFileName
			)

		return commands

	"""
	ST2/ST3-compatible wrapper for getting the project file for a window, made possible with
	titoBouzout's getProjectFile method (refactored to __project_file_name)
	"""
	def project_file_name(self, window):
		if hasattr(window, "project_file_name"):
			return window.project_file_name()
		return self.__project_file_name(window)

	"""
	ST2/ST3-compatible wrapper for getting the project data for a window as a dictionary, made possible with
	titoBouzout's getProjectFile method (refactored to __project_file_name)
	"""
	def project_data(self, window):
		if hasattr(window, "project_data"):
			return window.project_data()

		# get the project file, returning None if it doesn't exist, just like ST3's get_project_file()
		projectFileName = self.project_file_name(window)
		if projectFileName is None:
			return None

		# read the project json file
		import json
		data = file(projectFileName, 'r').read()
		data = data.replace('\t', ' ')
		return json.loads(data, strict=False)

	def is_string(self, var):
		if sys.version_info >= (3, 0, 0):
			return isinstance(var, str)
		return isinstance(var, str) or isinstance(var, unicode)

	def __build_commands(self, fido, path, getAll = False, fileName = None, projectBasePath = None):
		# build the command
		commands = []
		command = None
		env = {}
		if self.is_string(fido):
			command = fido
			alwaysRun = True if getAll else False
		elif isinstance(fido, list) and getAll:
			for f in fido:
				commands += self.__build_commands(f, path, getAll = getAll, fileName = fileName, projectBasePath = projectBasePath)
		elif (isinstance(fido, dict) and fido.get('command')):
			if 'path' in fido:
				if fileName != None:
					# see if the file is within the path
					if self.is_string(fido['path']):
						paths = [fido['path']]
					elif isinstance(fido['path'], list):
						paths = fido['path']
					else:
						paths = []

					for aProjectPath in paths:
						if os.path.isabs(aProjectPath) != True and projectBasePath != None:
							aProjectPath = os.path.join(projectBasePath, aProjectPath)
						if fido.get('follow_symlinks', False):
							aProjectPath = os.path.realpath(aProjectPath)
							testFileName = os.path.realpath(fileName)
						else:
							testFileName = fileName
						if os.path.commonprefix([aProjectPath, testFileName]) == aProjectPath:
							path = aProjectPath
							command = fido['command']
							alwaysRun = fido.get('alwaysRun', False) or getAll
							env = fido.get('env', {})
							break
			else:
				command = fido['command']
				alwaysRun = fido.get('alwaysRun', False) or getAll
				env = fido.get('env', {})

		if command != None and alwaysRun: commands.append({'path': path, 'command': command, 'env': env})

		return commands

	"""
	Original method getProjectFile by titoBouzout, author of SideBarEnhancements
	https://github.com/titoBouzout/SideBarEnhancements/blob/master/sidebar/SideBarProject.py
	"""
	def __project_file_name(self, window):
		if not window.folders():
			return None
		import json, re
		data = file(os.path.normpath(os.path.join(sublime.packages_path(), '..', 'Settings', 'Session.sublime_session')), 'r').read()
		data = data.replace('\t', ' ')
		data = json.loads(data, strict=False)
		projects = data['workspaces']['recent_workspaces']

		if os.path.lexists(os.path.join(sublime.packages_path(), '..', 'Settings', 'Auto Save Session.sublime_session')):
			data = file(os.path.normpath(os.path.join(sublime.packages_path(), '..', 'Settings', 'Auto Save Session.sublime_session')), 'r').read()
			data = data.replace('\t', ' ')
			data = json.loads(data, strict=False)
			if hasattr(data, 'workspaces') and hasattr(data['workspaces'], 'recent_workspaces') and data['workspaces']['recent_workspaces']:
				projects += data['workspaces']['recent_workspaces']
			projects = list(set(projects))
		for project_file in projects:
			project_file = re.sub(r'^/([^/])/', '\\1:/', project_file);
			project_json = json.loads(file(project_file, 'r').read(), strict=False)
			if 'folders' in project_json:
				folders = project_json['folders']
				found_all = True
				for directory in window.folders():
					found = False
					for folder in folders:
						folder_path = re.sub(r'^/([^/])/', '\\1:/', folder['path']);
						if folder_path == directory.replace('\\', '/'):
							found = True
							break;
					if found == False:
						found_all = False
						break;
			if found_all:
				return project_file
		return None

class FidoEventListener(sublime_plugin.EventListener):
	def on_post_save(self, view):
		fu = FidoUtils()
		window = view.window()
		projectFileName = fu.project_file_name(window)
		if projectFileName is None: return

		project = fu.project_data(window).copy()
		projectBasePath = os.path.dirname(projectFileName)

		defaultFido = project.get('fido', None)
		savedFileName = view.file_name()

		# get commands
		commands = fu.get_commands(project, projectBasePath, savedFileName)

		# run 'em
		FidoCommandThread(commands).start()

class FidoCommandThread(threading.Thread):
	def __init__(self, commands):
		self.__commands = commands
		threading.Thread.__init__(self)

	def run(self):
		for command in self.__commands:
			env = os.environ.copy()
			env.update(command.get('env', {}))
			print('fido$ ' + str(command.get('command')))
			output = subprocess.Popen(
				command.get('command'), shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
				cwd=command.get('path', None), env=env
			).communicate()[0]
			if hasattr(output, 'decode'): output = output.decode('utf-8')
			print(output)
