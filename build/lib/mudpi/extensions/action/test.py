""" Test Interface """
from . import NAMESPACE


class Interface:

	namespace = NAMESPACE

	def __init__(self, mudpi):
		self.mudpi = mudpi

	def init(self, config):
		self.config = config
		return True