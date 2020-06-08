"""
Copyright (c) 2019, 2020 Genome Research Limited

Author: Christopher Harrison <ch12@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see https://www.gnu.org/licenses/
"""

import logging
import sys
from enum import Enum
from functools import partial
from getpass import getuser
from traceback import print_tb
from types import TracebackType

from . import typing as T, time


class Level(Enum):
    """ Convenience enumeration for logging levels """
    Debug    = logging.DEBUG
    Info     = logging.INFO
    Warning  = logging.WARNING
    Error    = logging.ERROR
    Critical = logging.CRITICAL


class _LoggableMixin:
    """ Base mixin class for logging interface """
    # NOTE The following can be either class or instance variables
    # NOTE _logger refers to a named logger with a set level; specifying
    # a different _level will change that value for that logger, but not
    # any handlers that have already been defined. This is a bit messy,
    # but it's to facilitate the easy definition of downstream mixins
    _logger:str
    _level:Level
    _formatter:logging.Formatter

    @property
    def logger(self) -> logging.Logger:
        logger = logging.getLogger(self._logger)
        logger.setLevel(self._level.value)
        return logger

    def _log(self, message:str, level:Level = Level.Info) -> None:
        """ Log a message at an optional level """
        self.logger.log(level.value, message)

    @property
    def log(self) -> object:
        """ End-user logging functions exposed as log.* """
        parent = self

        class _wrapper:
            @staticmethod
            def debug(message:str) -> None:
                # Convenience alias
                parent._log(message, Level.Debug)

            @staticmethod
            def info(message:str) -> None:
                # Convenience alias
                parent._log(message, Level.Info)

            @staticmethod
            def warning(message:str) -> None:
                # Convenience alias
                parent._log(message, Level.Warning)

            @staticmethod
            def error(message:str) -> None:
                # Convenience alias
                parent._log(message, Level.Error)

            @staticmethod
            def critical(message:str) -> None:
                # Convenience alias
                parent._log(message, Level.Critical)

            def add_handler(self, handler:logging.Handler, formatter:T.Optional[logging.Formatter] = None, level:T.Optional[Level] = None) -> None:
                # TODO Don't add the same handler more than once
                handler.setFormatter(formatter or parent._formatter)
                handler.setLevel((level or parent._level).value)
                parent.logger.addHandler(handler)

            def to_tty(self, formatter:T.Optional[logging.Formatter] = None, level:T.Optional[Level] = None) -> None:
                # Convenience alias
                self.add_handler(logging.StreamHandler(), formatter, level)

            def to_file(self, filename:T.Path, formatter:T.Optional[logging.Formatter] = None, level:T.Optional[Level] = None) -> None:
                # Convenience alias
                self.add_handler(logging.FileHandler(filename), formatter, level)

        return _wrapper()


def _set_exception_handler(loggable:T.Type[_LoggableMixin]) -> None:
    """
    Create an exception handler that logs uncaught exceptions (except
    keyboard interrupts) and spews the traceback to stderr (in debugging
    mode) before terminating

    @param   loggable  Loggable mixin class
    """
    def _log_uncaught_exception(exc_type:T.Type[Exception], exc_val:Exception, traceback:TracebackType) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_val, traceback)

        else:
            loggable().log.critical(str(exc_val) or exc_type.__name__)
            if __debug__:
                print_tb(traceback)

            sys.exit(1)

    sys.excepthook = _log_uncaught_exception


def _to_tty(loggable:T.Type[_LoggableMixin]) -> None:
    """
    Add a stream handler to the specified loggable mixin

    @param   loggable  Loggable mixin class
    """
    loggable().log.to_tty()


class base(T.SimpleNamespace):
    """ Namespace of base classes to make importing easier """
    LoggableMixin = _LoggableMixin


class utils(T.SimpleNamespace):
    """ Namespace of utilities to make importing easier """
    make_format           = partial(logging.Formatter, datefmt=time.ISO8601)
    set_exception_handler = _set_exception_handler
    to_tty                = _to_tty


class formats(T.SimpleNamespace):
    """ Namespace of formatters to make importing easier """
    default = utils.make_format("%(asctime)s\t%(levelname)s\t%(message)s")
    with_username = utils.make_format(f"%(asctime)s\t%(levelname)s\t{getuser()}\t%(message)s")


class levels(T.SimpleNamespace):
    """ Namespace of levels to make importing easier """
    default = Level.Debug if __debug__ else Level.Info
