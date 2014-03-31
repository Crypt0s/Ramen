#!/usr/bin/python
import glob

pylist = glob.glob('libramen/*.py')
pylist = [item[:-3].split('/')[1] for item in pylist]
pylist.remove('__init__')

__all__ = pylist
