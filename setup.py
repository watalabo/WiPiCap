from distutils.core import setup, Extension
from Cython.Build import cythonize
from numpy import get_include

ext = Extension("wipicap", sources=["backends.pyx"], include_dirs=[get_include()])
setup(name = "wipicap", ext_modules = cythonize(ext))
