#-*- coding:utf-8 -*-

import os
import re
import sympy as sp
from pytuning.tuning_tables import *

class TuningTable(object):
    """
    Represents a set of tuned pitches within a tuning system. This consists of a scale, together with "anchoring"
    parameters, such as the reference note. Provides I/O methods for different tuning table formats.

    :param scale: The scale to be used to construct the tuning table. A list of rational or floating point values.
    :type scale: list(sp.core.numbers)
    :param description: The textual description of the scale and it's tuning system.
    :type description: str
    :param reference_note: The MIDI note number that is used as a datum starting pitch for the tuning scale.
    :type reference_note: int
    :param reference_frequency: The frequency in Hertz of the starting pitch of the tuning scale.
    :type reference_frequency: float
    """

    cents_pattern = re.compile('([0-9]*\.[0-9]*)')
    rational_pattern = re.compile('([0-9]* *\/ *[0-9]*)')
    
    def __init__(self, scale = None, description = '', reference_note = 69, reference_frequency = 440.0):
        self.description = description
        self.scale = [] if scale is None else scale
        self.reference_note = reference_note
        self.reference_frequency = reference_frequency

    def __repr__(self):
        return "<{} {} {}>".format(self.__class__.__name__, self.scale, self.description)
        
    def read_scala_file(self, file_path):
        """
        Read a named [Scala file format](https://www.huygens-fokker.org/scala/scl_format.html) file.
        
        :param file_path: Path to the Scala file to read.
        :type file_path: str
        :returns: True if able to read correctly, False if there was an error.
        :rtype: bool
        """
        state = 'read_description' # Uses a state machine for parsing the Scala file.
        # There is an implicit 1/1 in the Scala file that we make explicit in the scale.
        self.scale = [sp.core.numbers.Integer(1)]
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

    def create_scala_kbm(self):
        """
        Create a Scala KBM keyboard mapping file.
        """
        notes_per_octave = len(self.scale)-1
        keyboard_mapping = f"""! Template for a keyboard mapping for {self.description}
!
! Size of map. The pattern repeats every so many keys:
{len(self.scale)-1}
! First MIDI note number to retune:
0
! Last MIDI note number to retune:
127
! Middle note where the first entry of the mapping is mapped to:
{self.reference_note}
! Reference note for which frequency is given:
{self.reference_note}
! Frequency to tune the above note to:
{self.reference_frequency}
! Scale degree to consider as formal octave (determines difference in pitch
! between adjacent mapping patterns):
{notes_per_octave}
! Mapping.
! The numbers represent scale degrees mapped to keys. The first entry is for
! the given middle note, the next for subsequent higher keys.
! For an unmapped key, put in an "x". At the end, unmapped keys may be left out.
"""
        keyboard_mapping += '\n'.join([str(note_number) for note_number in range(notes_per_octave)])
        return keyboard_mapping

    def write_file(self, file_path, format = 'Scala', keyboard_file_path = None):
        """
        Writes the tuning table to the named file according to the format:
        
        - 'Scala': [Scala file format](https://www.huygens-fokker.org/scala/scl_format.html).
        - 'Timidity': Timidity file format.
        - 'Csound': Csound tuning declarations.
        - 'Fluidsynth': Fluidsynth tuning file format.
        """
        kbm_file_contents = ''  # Default to no KBM
        # Generate the output as a string, then write it.
        if format == 'Scala':
            file_contents = create_scala_tuning(self.scale, self.description)
            kbm_file_contents = self.create_scala_kbm()
        elif format == 'Timidity':
            file_contents = create_timidity_tuning(self.scale, self.reference_note)
        elif format == 'Csound':
            file_contents = create_csound_tuning(self.scale, reference_note = self.reference_note)
        elif format == 'Fluidsynth':
            file_contents = create_fluidsynth_tuning(self.scale, reference_note = self.reference_note)
        else:
            raise Exception(f"Unknown format {format}")
        with open(file_path, 'w') as file_handle:
            file_handle.write(file_contents)
            file_handle.write('\n') # Write final newline.
        if keyboard_file_path is not None:
            with open(keyboard_file_path, 'w') as file_handle:
                file_handle.write(kbm_file_contents)
                file_handle.write('\n') # Write final newline.
        return True

