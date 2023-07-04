import os.path
from ginga.misc.Bunch import Bunch

# my plugins are available here
p_path = os.path.split(__file__)[0]

def setup_FindImage():
    spec = Bunch(path=os.path.join(p_path, 'FindImage.py'),
                 module='FindImage', klass='FindImage',
                 ptype='local', workspace='dialogs', start=False,
                 category="Planning", menu="FindImage", tab='FindImage')
    return spec

def setup_InsFov():
    spec = Bunch(path=os.path.join(p_path, 'InsFov.py'),
                 module='InsFov', klass='InsFov',
                 ptype='local', workspace='dialogs', start=False,
                 category="Planning", menu="InsFov", tab='InsFov')
    return spec

def setup_PolarSky():
    spec = Bunch(path=os.path.join(p_path, 'PolarSky.py'),
                 module='PolarSky', klass='PolarSky',
                 ptype='local', workspace='dialogs', start=False,
                 category="Planning", menu="PolarSky", tab='PolarSky')
    return spec

def setup_TelescopePosition():
    spec = Bunch(path=os.path.join(p_path, 'TelescopePosition.py'),
                 module='TelescopePosition', klass='TelescopePosition',
                 ptype='local', workspace='dialogs', start=False,
                 category="Planning", menu="TelescopePosition", tab='TelPos')
    return spec

def setup_SkyCam():
    spec = Bunch(path=os.path.join(p_path, 'SkyCam.py'),
                 module='SkyCam', klass='SkyCam',
                 ptype='local', workspace='dialogs', start=False,
                 category="Planning", menu="SkyCam", tab='SkyCam')
    return spec

def setup_Targets():
    spec = Bunch(path=os.path.join(p_path, 'Targets.py'),
                 module='Targets', klass='Targets',
                 ptype='local', workspace='in:toplevel', start=False,
                 category="Planning", menu="Targets", tab='Targets')
    return spec

def setup_Visibility():
    spec = Bunch(path=os.path.join(p_path, 'Visibility.py'),
                 module='Visibility', klass='Visibility',
                 ptype='local', workspace='in:toplevel', start=False,
                 category="Planning", menu="Visibility", tab='Visibility')
    return spec

def setup_SiteSelector():
    spec = Bunch(path=os.path.join(p_path, 'SiteSelector.py'),
                 module='SiteSelector', klass='SiteSelector',
                 ptype='local', workspace='dialogs', start=False,
                 category="Planning", menu="Site Selector", tab='Site Selector')
    return spec

def setup_HSCPlanner():
    spec = Bunch(path=os.path.join(p_path, 'HSCPlanner.py'),
                 module='HSCPlanner', klass='HSCPlanner',
                 ptype='local', workspace='dialogs', start=False,
                 category="Planning", menu="HSCPlanner", tab='HSCPlanner')
    return spec
