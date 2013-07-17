# Fido

Fido is a plugin for Sublime Text (versions 2 and 3) for running commands when files within a project are saved.

## Installation
The easy way is to use [Package Control](http://wbond.net/sublime_packages/package_control).

The "hard" way is to install Fido manually using git. First, go to your `Packages` subdirectory under Sublime Text's data directory:
* Windows `%APPDATA%\Sublime Text 2` or `%APPDATA%\Sublime Text`
* OS X: `~/Library/Application Support/Sublime Text 2` or `~/Library/Application Support/Sublime Text`
* Linux `~/.config/sublime-text-2` or `~/.config/sublime-text`
* Portable Installation: `Sublime Text 2/Data` or `Sublime Text/Data`

Then clone this repository:

```git clone git://github.com/nerdo/fido.git```

## Usage

Fido works by looking for things to do in your project whenever a file is saved. The simplest setup is to have a top-level fido command that is run whenever a file is saved on any of the paths defined within your project. For example, your project file may look like this:

```javascript
{
    "folders":
	[
		{
			"follow_symlinks": true,
			"path": "/my/sublime/project"
		},
        {
            "path": "/another/path"
        }
	],
    "fido": "cake build"
}
```

This configuration runs `cake build` when a file is saved on one of the project paths defined by `folders`. The command sets the working directory to the folder the saved file was found on, so if you saved a file in `/another/path/scripts/file.coffee`, the `cake build` is run from `/another/path`.

You can see Fido at work if you open your console.

```
fido$ cake build
This is the output of cake build!
```

You can also set separate commands for each folder:

```javascript
{
    "folders":
    [
		{
			"follow_symlinks": true,
			"path": "/my/sublime/project",
            "fido": "cake build"
		},
        {
            "path": "/another/path",
            "fido": "rm -f ./tmp/generated-output.txt"
        }
	]
}
```

In this example, `cake build` is only run when a file in `/my/sublime/project` is saved. When a file is saved. When a file is saved on the path `/another/path`, the file `/another/path/tmp/generated-output.txt` is deleted with the command `rm -f ./tmp/generated-output.txt`.

What if you wanted to run `cake build` on all paths, but only remove that temp file when files within `/another/path` is saved? No problem. Define your settings like this:

```javascript
{
    "folders":
    [
    	{
			"follow_symlinks": true,
			"path": "/my/sublime/project"
		},
        {
            "path": "/another/path",
            "fido": "rm -f ./tmp/generated-output.txt"
        }
	],
    "fido": {
        "command": "cake build",
        "alwaysRun": true
    }
}
```

In this scenario, the Fido command is defined as an object with the properties `command` and `alwaysRun`.

If `alwaysRun` was set to false (the default), the command would not run when a more specific command is found (like the removal of the temp file).

Most projects are set up with a single folder, but you may want to run different commands for files saved in different parts of the project. That can be accomplished by setting up fido as an array. A more real-world project might look something like this:

```javascript
{
    "folders":
    [
        {
			"follow_symlinks": true,
			"path": "/my/sublime/project"
		},
	],
    "fido": [
        {
            "follow_symlinks": true,
            "path": "/my/sublime/project/scripts/coffee",
            "command": "cake build"
        },
        {
            "path": "/my/sublmime/project/scss",
            "command": "sass --style compressed site.scss ../css/site.css"
        },
        {
            "command": "growlnotify -m'Insanely annoying message every time a file is saved' -t'Annoying Notification'",
            'alwaysRun': true
        }
    ]
}
```

This sets up Fido to run a few commands. First, `cake build` runs when files are saved on the path `/my/sublime/projects/scripts/coffee`. Note the `follow_symlinks` option has the same meaning as when it is defined in a folder.

Then there is a `sass` command that gets run to recompile an scss file into css when files are saved on its path.

Last, but not least, there is a command that is run on every file saved within the project which runs `growlnotify`, for no apparent reason... Ok, so this isn't **completely** a real-world example :P

Because most people don't normally launch sublime from the command line, it's likely that your environment path won't be set as you expect it. For example, you may see something like this in your console if you were trying to run `cake build`:

```
fido$ cake build
/bin/sh: cake: command not found
```

If you get errors like this, you'll need to set your environment path, open a terminal and check your `PATH` variable.

In OS X and *nix: `echo $PATH`

Copy that value, and set it up like so:

```javascript
{
    "folders":
    [
        {
    		"follow_symlinks": true,
			"path": "/my/sublime/project"
		},
	],
    "fido": [
        {
            "follow_symlinks": true,
            "path": "/my/sublime/project/scripts/coffee",
            "command": "cake build",
            "env": {
                "PATH": "<<< PATH COPIED FROM COMMAND LINE HERE >>>"
            }
        },
        {
            "path": "/my/sublmime/project/scss",
            "command": "sass --style compressed site.scss ../css/site.css",
            "env": {
                "PATH": "<<< PATH COPIED FROM COMMAND LINE HERE >>>"
            }
        },
        {
            "command": "growlnotify -m'Insanely annoying message every time a file is saved' -t'Annoying Notification'",
            'alwaysRun': true,
            "env": {
                "PATH": "<<< PATH COPIED FROM COMMAND LINE HERE >>>"
            }
        }
    ]
}
```

You may or may not need to set the path depending on where the command lives on your filesystem, but it's probably a good idea to include it with each command.

By the way, any environment variables can be set this way by setting key-value pairs on the env object, not **just** PATH.

## Special Thanks
Special thanks go out to [titoBouzout]: https://github.com/titoBouzout for letting me use a piece of his code from his [SideBarEnhancements]: https://github.com/titoBouzout/SideBarEnhancements to get this working properly on ST2.
