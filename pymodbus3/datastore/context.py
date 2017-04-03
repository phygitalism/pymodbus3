# -*- coding: utf-8 -*-

from pymodbus3.exceptions import ParameterException
from pymodbus3.interfaces import IModbusSlaveContext
from pymodbus3.datastore.store import ModbusSequentialDataBlock
from pymodbus3.constants import Defaults

# Logging
import logging
_logger = logging.getLogger(__name__)


class ModbusSlaveContext(IModbusSlaveContext):
    """
    This creates a modbus data model with each data access
    stored in its own personal block
    """

    def __init__(self, *args, **kwargs):
        """ Initializes the datastores, defaults to fully populated
        sequential data blocks if none are passed in.

        :param kwargs: Each element is a ModbusDataBlock

            'di' - Discrete Inputs initializer
            'co' - Coils initializer
            'hr' - Holding Register initializer
            'ir' - Input Registers initializer
        """
        self.store = dict()
        self.store['d'] = kwargs.get('di', ModbusSequentialDataBlock.create())
        self.store['c'] = kwargs.get('co', ModbusSequentialDataBlock.create())
        self.store['i'] = kwargs.get('ir', ModbusSequentialDataBlock.create())
        self.store['h'] = kwargs.get('hr', ModbusSequentialDataBlock.create())

    def __str__(self):
        """ Returns a string representation of the context

        :returns: A string representation of the context
        """
        return "Modbus Slave Context"

    def reset(self):
        """ Resets all the datastores to their default values """
        for datastore in self.store.values():
            datastore.reset()

    def validate(self, fx, address, count=1):
        """ Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        address += 1  # section 4.4 of specification
        _logger.debug('validate[{0}] {1}:{2}'.format(fx, address, count))
        return self.store[self.decode(fx)].validate(address, count)

    def get_values(self, fx, address, count=1):
        """ Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        address += 1  # section 4.4 of specification
        _logger.debug('get_values[{0}] {1}:{2}'.format(fx, address, count))
        return self.store[self.decode(fx)].get_values(address, count)

    def set_values(self, fx, address, values):
        """ Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        address += 1  # section 4.4 of specification
        _logger.debug('set_values[{0}] {1}:{2}'.format(
            fx, address, len(values)
        ))
        self.store[self.decode(fx)].set_values(address, values)


class ModbusServerContext(object):
    """ This represents a master collection of slave contexts.
    If single is set to true, it will be treated as a single
    context so every unit-id returns the same context. If single
    is set to false, it will be interpreted as a collection of
    slave contexts.
    """

    def __init__(self, slaves=None, single=True):
        """ Initializes a new instance of a modbus server context.

        :param slaves: A dictionary of client contexts
        :param single: Set to true to treat this as a single context
        """
        self.single = single
        self.__slaves = slaves or {}
        if self.single:
            self.__slaves = {Defaults.UnitId: self.__slaves}

    def __iter__(self):
        """ Iterate over the current collection of slave
        contexts.

        :returns: An iterator over the slave contexts
        """
        return self.__slaves.items()

    def __contains__(self, slave):
        """ Check if the given slave is in this list

        :param slave: slave The slave to check for existence
        :returns: True if the slave exists, False otherwise
        """
        return slave in self.__slaves

    def __setitem__(self, slave, context):
        """ Used to set a new slave context

        :param slave: The slave context to set
        :param context: The new context to set for this slave
        """
        if self.single:
            slave = Defaults.UnitId
        if 0xf7 >= slave >= 0x00:
            self.__slaves[slave] = context
        else:
            raise ParameterException('slave index out of range')

    def __delitem__(self, slave):
        """ Wrapper used to access the slave context

        :param slave: The slave context to remove
        """
        if not self.single and (0xf7 >= slave >= 0x00):
            del self.__slaves[slave]
        else:
            raise ParameterException('slave index out of range')

    def __getitem__(self, slave):
        """ Used to get access to a slave context

        :param slave: The slave context to get
        :returns: The requested slave context
        """
        if self.single:
            slave = Defaults.UnitId
        if slave in self.__slaves:
            return self.__slaves.get(slave)
        else:
            raise ParameterException(
                'slave does not exist, or is out of range'
            )