""" 
	Custom Extension Example
	Provide a good description of what
	your extension is adding to MudPi
	or what it does.
"""
from mudpi.extensions import BaseExtension


# Your extension should extend the BaseExtension class
class Extension(BaseExtension):
	# The minimum your extension needs is a namespace. This
	# should be the same as your folder name and unique for
	# all extensions. Interfaces all components use this namespace.
	namespace = 'grow'

	# You can also set an update interval at which components
	# should be updated to gather new data / state.
	update_interval = 1

	def init(self, config):
		""" Prepare the extension and all components """
		# This is called on MudPi start and passed config on start.
		# Here is where devices should be setup, connections made,
		# components created and added etc.

		# Must return True or an error will be assumed disabling the extension
		return True

	def validate(self, config):
		""" Validate the extension configuration """
		# Here the extension configuration is passed in before the init() method
		# is called. The validate method is used to prepare a valid configuration
		# for the extension before initialization. This method should return the
		# validated config or raise a ConfigError.

		return config
