#
# linter.py
# Linter for SublimeLinter3, a code checking framework for Sublime Text 3 (Java)
#
# Written by Ganesha <reekoheek@gmail.com>
# Copyright (c) 2013 Ganesha <reekoheek@gmail.com>
#
# License: MIT
#

"""This module exports the Java plugin class."""

import os
import glob
import shutil
import tempfile
import re
from SublimeLinter.lint import Linter, util


class Java(Linter):

    """Provides an interface to java."""

    syntax = ('java')
    # change to None to use fn
    cmd = None
    executable = 'javac'
    # regex = r'^.+?:(?P<line>\d+):\s*(?:(?P<warning>warning)|(?P<error>error)):\s*(?P<message>.+)'
    # multiline = False
    head_regex = r'^.+?:(?P<line>\d+):\s*(?:(?P<warning>warning)|(?P<error>error)):\s*(?P<message>.+)$'
    regex = r'''(?xi)
        # First line is (lineno): type: error message
        ^.+?:(?P<line>\d+):\s*(?:(?P<warning>warning)|(?P<error>error)):\s*(?P<message>.+)$\r?\n

        # Second line is the line of code
        ^.*$\r?\n

        # Third line is a caret pointing to the position of the error
        ^(?P<col>[^\^]*)\^$
    '''
    multiline = True
    line_col_base = (1, 1)
    tempfile_suffix = 'java'
    error_stream = util.STREAM_STDERR
    selectors = {}
    word_re = None
    defaults = {}
    inline_settings = None
    inline_overrides = None
    comment_re = None

    def cmd(self):
        """
        Return a string with the command line to execute.

        We define this method because we want to use the .jshintrc files,
        and we can't rely on jshint to find them, because we are using stdin.

        """

        settings = self.get_view_settings()

        directory = settings.get("directory")

        # sometimes settings does not read from project settings and directory is empty
        if directory == None:
            return []

        command = [self.executable_path, '-Xlint', '-d', directory]

        classpath = settings.get("classpath")

        if isinstance(classpath, str):
            classpath = classpath
        elif classpath == None:
            classpath = ""
        elif all(isinstance(item, str) for item in classpath): # check iterable for stringness of all items. Will raise TypeError if some_object is not iterable
            classpath = ":".join(classpath)
        else:
            classpath = ""

        if classpath != "":
            command += ['-cp', classpath]

        # command += ['-source', '1.5']
        command += ['@']

        # print(command)

        return command

    def tmpfile(self, cmd, code, suffix=''):
        """Run an external executable using a temp file to pass code and return its output."""

        filename = os.path.basename(self.filename)

        try:
            cmd = list(cmd)


            if '@' in cmd:
                cmd[cmd.index('@')] = self.filename
            else:
                cmd.append(f.name)

            # print(' '.join(cmd))

            out = util.popen(cmd, output_stream=self.error_stream)
            if out:
                out = out.communicate()
                filtered = ''
                skip = 0
                lines = util.combine_output(out).split('\n')

                errline = []
                for line in lines:
                    # print("line:", line)
                    if line == '':
                        continue

                    match = re.match(r'warning: \[path\] bad path element', line)
                    if match:
                        filtered += self.filename + ":1: " + line + "\n\n\n"
                        continue

                    if skip > 0:
                        skip = skip - 1
                    else:
                        match = re.match(self.head_regex, line)
                        if match:
                            # print("errline:", errline)
                            if len(errline) > 0:
                                filtered += errline[0];
                                if len(errline) > 3:
                                    filtered += ", " + (errline[3].strip())
                                if len(errline) > 4:
                                    filtered += ", " + (errline[4].strip())
                                filtered += "\n"
                                filtered += errline[1] + "\n"
                                filtered += errline[2] + "\n"
                            errline = []

                        if match and (not self.filename in line):
                            skip = 2
                        else:
                            errline.append(line)

                if len(errline) > 0:
                    filtered += errline[0];
                    if len(errline) > 3:
                        filtered += ", " + (errline[3].strip())
                    if len(errline) > 4:
                        filtered += ", " + (errline[4].strip())
                    filtered += "\n"
                    filtered += errline[1] + "\n"
                    filtered += errline[2] + "\n"
                # print("-------------")
                # print(filtered)
                # print("-------------")
                return filtered
                # return util.combine_output(out)
            else:
                return ''
        # except:
        #     pass
        finally:
            pass
            # shutil.rmtree(d, True)
