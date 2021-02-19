from mudpi.workers import Worker
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.constants import DEFAULT_UPDATE_INTERVAL

class InterfaceManager:

    def __init__(self, 
        mudpi, 
        namespace,
        interface_name,
        interface, 
        update_interval = DEFAULT_UPDATE_INTERVAL
    ):
        self.mudpi = mudpi
        self.namespace = namespace
        self.interface_name = interface_name
        self.interface = interface
        self.update_interval = update_interval

        self.config = None
        self.workers = {}
        self.worker = self.add_worker()

        mudpi.cache.setdefault('interface_managers', {})[namespace] = self

    def init(self, config):
        """ Init the interface worker with the configurations """
        if hasattr(self.interface, 'Interface'):
            self._interface = self.interface.Interface(mudpi)
            try:
                if self.interface.Interface.init == self.interface.Interface.__bases__[0].init:
                    Logger.log(
                        LOG_LEVEL["debug"], f"Extension {self.namespace} Interface {self.interface_name} did not define init() method."
                    )
                init_result = self._interface.init(config)
            except AttributeError as error:
                Logger.log(
                    LOG_LEVEL["debug"], f"Extension {self.namespace} Interface {self.interface_name} did not extend ExtensionInterface."
                )
                return False

        return True

    def add_worker(self, config = {}):
        """ Load up a worker and add it to the manager """
        worker_name = f"{self.namespace}.{self.interface_name}.{self.update_interval}"
        if worker_name in self.workers:
            return self.workers[worker_name]

        cache = self.mudpi.cache.setdefault("workers", {})

        self.workers[worker_name] = cache[worker_name] = Worker(self.mudpi, {'key': worker_name})
        return self.workers[worker_name]

    def add_component(self, component):
        """ Add the component to the interfaces worker """
        try:
            if component.id is None:
                Logger.log(
                    LOG_LEVEL["debug"], f"Extension {self.namespace} Interface {self.interface_name} component did not define `id`."
                )
                return False

            if component.id in self.worker.components:
                Logger.log(
                    LOG_LEVEL["debug"], f"Extension {self.namespace} Interface {self.interface_name} component id already registered."
                )
                return False

            self.worker.components[component.id] = self.mudpi.components.register(component.id, component)
            component.component_registered(mudpi=self.mudpi, interface=self)
            return True
        except Exception as error:
            Logger.log(
                LOG_LEVEL["debug"], f"Extension {self.namespace}:{self.interface_name} unknown error adding component.\n{error}"
            )

    def __repr__(self):
        """ Representation of the manager. (Handy for debugging) """
        return f"<InterfaceManager {self.namespace}:{self.interface_name} @ {self.update_interval}s>"