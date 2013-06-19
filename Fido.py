import sublime, sublime_plugin, os, subprocess

class FidoEventListener(sublime_plugin.EventListener):
	def on_post_save(self, view):
		projectFileName = view.window().project_file_name()
		if projectFileName is None: return

		# check to see if the view's project has a fido command
		project = view.window().project_data().copy()

		# if 'fido' not in project or 'command' not in project['fido'] or 'folders' not in project: return
		if 'fido' in project:
			defaultFido = project['fido']
		else:
			defaultFido = None

		savedFileName = view.file_name()
		projectBasePath = os.path.dirname(projectFileName)

		# make sure the file is on the project path
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
				if (isinstance(fido, str)):
					command = fido
					# shell = False
				elif (isinstance(fido, dict) and 'command' in fido):
					command = fido['command']
					# shell = True if ('shell' in fido and fido['shell']) else False

				# run it
				if (command is not None):
					print('# ' + command)
					subprocess.call(command, shell=True)
