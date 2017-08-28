'''setup.py
'''

from distutils.core import setup

setup(
  name = 'result_py',
  packages = ['result_py'],
  version = '0.1.0',
  description = 'A Result type much like Rust\'s, featuring generics and lovely combinators.',
  author = 'Zack Mullaly',
  author_email = 'zsck@riseup.net',
  url = 'https://github.com/zsck/result_py', # use the URL to the github repo
  download_url = 'https://github.com/peterldowns/mypackage/archive/0.1.tar.gz', # I'll explain this in a second
  keywords = ['rust', 'result', 'generics', 'type hinting'], # arbitrary keywords
  classifiers = [
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)