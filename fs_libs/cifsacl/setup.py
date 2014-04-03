from distutils.core import setup, Extension

module1 = Extension('cifsacl',
                    sources = ['cifsaclmodule.c'],
                    include_dirs=['./include','./'],
                    library_dirs=['./'],
                    #libraries=['getcifsacl'],
                    )

setup (name = 'CIFSacl',
       version = '1.0',
       description = 'Python binding of the cifs ACL tools',
       ext_modules = [module1])
