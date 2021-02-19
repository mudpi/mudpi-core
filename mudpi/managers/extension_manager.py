from mudpi import importer, utils
from mudpi.exceptions import MudPiError
from mudpi.constants import DEFAULT_UPDATE_INTERVAL
from mudpi.managers.interface_manager import InterfaceManager

class ExtensionManager:
	""" Extension Manager

		Controls components and interfaces for an extensions.
		Helps setup new interfaces and coordinate workers for
		any components.
	"""

	def __init__(self, mudpi, namespace, update_interval = DEFAULT_UPDATE_INTERVAL):
		self.mudpi = mudpi
		self.namespace = namespace
		self.update_interval = update_interval if update_interval is not None else DEFAULT_UPDATE_INTERVAL
		# Config gets set in the `init()` because not all extensions have base config
		self.config = None
		self.interfaces = {}
		# Create an default interface for the extension components without interfaces 
		self.interfaces[namespace] = self.init_interface(namespace, {})
		self.importer = importer.get_extension_importer(self.mudpi, self.namespace)

		mudpi.cache.setdefault('extension_managers', {})[namespace] = self

	""" Properties """
	@property
	def components(self):
		""" Returns a list of all components for all interfaces """
		return [ component
			for interface in self.interfaces
			for worker in interface.workers 
			for component in worker.components ]
	
	""" Methods """
	def init(self, config):
		""" Loads in configs and prepares the manager """
		self.config = config

		# LOAD ALL THE CONFIGS AS INTERFACES
	
	def init_interface(self, interface_name, interface, update_interval = None):
		""" Create a new interface manager and return it """
		if update_interval is None:
			update_interval = self.update_interval
		return InterfaceManager(self.mudpi, self.namespace, interface_name, interface, update_interval)

	def add_component(self, component, interface_name=None):
		""" Register a component using the specified interface. """
		interface_name = interface_name or self.namespace
		if interface_name not in self.interfaces:
			raise MudPiError(f"Attempted to add_component to interface {interface_name} that doesn't exist.")

		if utils.is_component(component):
			return self.interfaces[interface_name].add_component(component)

		raise MudPiError(f"Passed non-component to add_component for {self.namesapce}.")

	def add_interface(self, interface_name, interface_config = {}):
		""" Add an interface for an Extension if it isn't loaded """

		if self.config is None:
			raise MudPiError("Config was null in extension manager. Call `init(config)` first.")
			return

		if interface_name in self.interfaces:
			return self.interfaces[interface_name]
			
		interface = self.importer.prepare_interface_for_import(interface_name)

		if not interface:
			raise MudPiError(f'Interface {interface_name} failed to prepare for import.')

		update_interval = interface_config.get('update_interval', self.update_interval)

		# Create a composite key based on interface and update intervals
		interface_key = f'{interface_name}.{update_interval}'

		if interface_key not in self.interfaces:
			self.interfaces[interface_key] = self.add_interface(interface_name, interface, update_interval)

		self.interfaces[interface_key].init(interface_config)

	def __repr__(self):
		""" Representation of the manager. (Handy for debugging) """
		return f"<ExtensionManager {self.namespace} @ {self.update_interval}s>"

