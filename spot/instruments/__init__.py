#
"""
NOTE: to add your telescope's instrument overlays, add a module to this
directory, import it here and assign it in inst_dict.  Follow examples in
subaru.py .
"""
inst_dict = dict()

# Subaru Telescope instruments
from .subaru import subaru_fov_dict
inst_dict['Subaru'] = subaru_fov_dict

# Your telescope here!
