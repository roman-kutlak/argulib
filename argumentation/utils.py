import os
import sys
import yaml
import logging
import inspect
import logging.config

# Logging code from:
#   http://victorlin.me/posts/2012/08/26/good-logging-practice-in-python
# format fields:
#   http://docs.python.org/3.3/library/logging.html#logrecord-attributes
#

# remove multiple spaces
def trim(str):
    return ' '.join(str.strip().split())


def log():
    """ Return the default program logger. """
    return logging.getLogger('argumentation')


class Settings:
    """ Class Settings reads a file with various settings such as paths to
        domain definition files, paths to file with plans, etc.

        """

    def __init__(self, filename):
        # assume the file contains key value pairs with no spaces
        self.table = dict()
        try:
            with open(filename) as f:
                for line in f:
                    kv = line.split()
                    if len(kv) > 1:
                        self.table[kv[0]] = kv[1]

        except IOError:
            # This should probably log the exception...
            print("Something wrong with the file '%s'" % filename)

    def get_setting(self, key):
        if key in self.table:
            return self.table[key]
        else:
            return None

"""
    Look for a default settings file in $HOME/.sassy/sassy.prefs
    and create a Settings object using that file.

    """
def get_user_settings():
    home = os.getenv("HOME")
    path = os.sep.join([home, ".sassy/sassy.prefs"])
    return Settings(path)


def try_setup_logging():
    config_path = default_config_file()
    if not (os.path.isfile(config_path) and os.access(config_path, os.R_OK)):
        config_path = find_config_file()
    setup_logging(config_path)


def setup_logging(
    default_path='log.config.yaml',
    default_level=logging.DEBUG,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        print('Using log config file "%s"' % path)
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    else:
        print('Could not open log config file "%s"' % path)
        logging.basicConfig(level=default_level)


def default_config_file():
    # read the config file
    if getattr(sys, 'frozen', False): # frozen
        mod_path = os.path.dirname(sys.executable)
    else: # unfrozen
        mod_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.sep.join([mod_path, 'resources', 'log.config.yaml'])
    return(config_path)


def find_config_file(cwd):
    # move 3 levels up and search
    start = '.'
    if 'Contents' in cwd:
        start = os.path.sep.join(['..', '..'])
    files = find_files(start, '.yaml')
    for root, file in files:
        if file == 'log.config.yaml':
            config_path = os.path.join(root, file)
    return config_path


def find_files(dir, extension):
    result = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(extension):
                 result.append( (root, file) )
    return result


MAC = True
try:
    from PyQt5.QtGui import qt_mac_set_native_menubar
except ImportError:
    MAC = False

#############################################################################
##
## Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
## All rights reserved.
##
## This file is part of SAsSy NLG library.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of University of Aberdeen nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################
