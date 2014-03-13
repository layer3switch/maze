""" maze behaviors modules"""
#print "\nPackage at%s" % __path__[0]

__all__ = ['behaving',]

for m in __all__:
    exec "from . import %s" % m  #relative import
