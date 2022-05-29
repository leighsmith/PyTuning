#-*- coding:utf-8 -*-

import os
import re
import sympy as sp
from pytuning.tuning_tables import create_scala_tuning, create_timidity_tuning

class TuningTable(object):
    """
    Represents a set of tuned pitches within a tuning system.
    Provides I/O methods for different tuning table formats.
    """
    def __init__(self):
        self.description = ''
        self.scale = []
        self.reference_note = 0
        self.cents_pattern = re.compile('([0-9]*\.[0-9]*)')
        self.rational_pattern = re.compile('([0-9]* *\/ *[0-9]*)')
        
    def read_scala_file(self, file_path):
        """
        Read a named [Scala file format](https://www.huygens-fokker.org/scala/scl_format.html) file.
        
        :param file_path: Path to the Scala file to read.
        :type file_path: str
        :returns: True if able to read correctly, False if there was an error.
        :rtype: bool
        """
        state = 'read_description' # Uses a state machine for parsing the Scala file.
        self.scale = []
        expected_scale_values = 0
        if os.path.exists(file_path):
            with open(file_path, 'r') as file_handle:
                for scale_line in file_handle:
                    if scale_line.strip()[0] == '!': # Comment line
                        continue
                    # We have a valid non-comment line, use state machine to determine
                    # what to do with it.
                    if state == 'read_description':
                        self.description = scale_line.strip()
                        state = 'read_scale_length'
                    elif state == 'read_scale_length':
                        expected_scale_values = int(scale_line)
                        state = 'read_scale_values'
                        scale_value_index = 0
                    elif state == 'read_scale_values':
                        # Determine the type of the value.
                        # If it has a period, it's a cents value.
                        # Anything after the number should be ignored.
                        # No negative values.
                        scale_value = scale_line.strip()
                        found_cents = self.cents_pattern.match(scale_value)
                        found_rational = self.rational_pattern.match(scale_value)
                        if found_cents is not None:
                            self.scale.append(sp.core.numbers.Float(found_cents.group(1)) / sp.core.numbers.Integer(1200))
                        elif found_rational is not None:
                            self.scale.append(sp.core.numbers.Rational(found_rational.group(1)))
                        scale_value_index += 1
                        if scale_value_index == expected_scale_values:
                            state = 'after_scale_values'
            return True
        return False

    def write_scala_file(self, file_path):
        """
        Writes the tuning table to the named [Scala file format](https://www.huygens-fokker.org/scala/scl_format.html) file.
        """
        scala_string = create_scala_tuning(self.scale, self.description)
        with open(file_path, 'w') as file_handle:
            file_handle.write(scala_string)
        return True

    def write_timidity_file(self, file_path):
        """
        Writes the tuning table to the named Timidity file.
        """
        timidity_string = create_timidity_tuning(self.scale, self.reference_note)
        with open(file_path, 'w') as file_handle:
            file_handle.write(timidity_string)
        return True
