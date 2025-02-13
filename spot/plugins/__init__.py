# import os.path
# from ginga.misc.Bunch import Bunch


# # my plugins are available here
# p_path = os.path.split(__file__)[0]


# def setup_SiteSelector():
#     spec = Bunch(path=os.path.join(p_path, 'SiteSelector.py'),
#                  module='SiteSelector', klass='SiteSelector',
#                  ptype='local', workspace='dialogs',
#                  category="Planning", menu="Site Selector", tab='Site',
#                  ch_sfx='_TGTS', index=0.0, enabled=True, exclusive=False)
#     return spec


# def setup_PolarSky():
#     spec = Bunch(path=os.path.join(p_path, 'PolarSky.py'),
#                  module='PolarSky', klass='PolarSky',
#                  ptype='local', workspace='dialogs',
#                  category="Planning", menu="PolarSky", tab='PolarSky',
#                  ch_sfx='_TGTS', index=1.0, enabled=True, exclusive=False)
#     return spec


# def setup_Targets():
#     spec = Bunch(path=os.path.join(p_path, 'Targets.py'),
#                  module='Targets', klass='Targets',
#                  ptype='local', workspace='in:toplevel',
#                  category="Planning", menu="Target List", tab='Targets',
#                  ch_sfx='_TGTS', index=2.0, enabled=True, exclusive=False)
#     return spec


# def setup_Visibility():
#     spec = Bunch(path=os.path.join(p_path, 'Visibility.py'),
#                  module='Visibility', klass='Visibility',
#                  ptype='local', workspace='in:toplevel',
#                  category="Planning", menu="Visibility Plot", tab='Visibility',
#                  ch_sfx='_TGTS', index=3.0, enabled=True, exclusive=False)
#     return spec


# def setup_SkyCam():
#     spec = Bunch(path=os.path.join(p_path, 'SkyCam.py'),
#                  module='SkyCam', klass='SkyCam',
#                  ptype='local', workspace='dialogs',
#                  category="Planning", menu="Sky Cams", tab='SkyCam',
#                  ch_sfx='_TGTS', index=4.0, enabled=True, exclusive=False)
#     return spec


# def setup_TargetGenerator():
#     spec = Bunch(path=os.path.join(p_path, 'TargetGenerator.py'),
#                  module='TargetGenerator', klass='TargetGenerator',
#                  ptype='local', workspace='in:toplevel',
#                  category="Planning", menu="Target Generator",
#                  tab='TargetGen',
#                  ch_sfx='_TGTS', index=5.0, enabled=True, exclusive=False)
#     return spec


# def setup_TelescopePosition():
#     spec = Bunch(path=os.path.join(p_path, 'TelescopePosition.py'),
#                  module='TelescopePosition', klass='TelescopePosition',
#                  ptype='local', workspace='dialogs',
#                  category="Planning", menu="Telescope Position", tab='TelPos',
#                  ch_sfx='_TGTS', index=6.0, enabled=False, exclusive=False)
#     return spec


# def setup_LGS():
#     spec = Bunch(path=os.path.join(p_path, 'LGS.py'),
#                  module='LGS', klass='LGS',
#                  ptype='local', workspace='dialogs',
#                  category="Planning", menu="LGS", tab='LGS',
#                  ch_sfx='_TGTS', index=7.0, enabled=False, exclusive=True),


# def setup_FindImage():
#     spec = Bunch(path=os.path.join(p_path, 'FindImage.py'),
#                  module='FindImage', klass='FindImage',
#                  ptype='local', workspace='dialogs',
#                  category="Planning", menu="Finding Chart", tab='FindImage',
#                  ch_sfx='_FIND', index=10.0, enabled=True, exclusive=False)
#     return spec


# def setup_InsFov():
#     spec = Bunch(path=os.path.join(p_path, 'InsFov.py'),
#                  module='InsFov', klass='InsFov',
#                  ptype='local', workspace='dialogs',
#                  category="Planning", menu="Instrument FOV", tab='InsFov',
#                  ch_sfx='_FIND', index=11.0, enabled=True, exclusive=False)
#     return spec
