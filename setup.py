from setuptools import setup

import shutil
import os

setup(name="tinman",
      version          = __import__('tinman').__version__,
      description      = "Testnet management scripts.",
      url              = "https://github.com/steemit/tinman",
      author           = "Steemit",
      packages         = ["tinman", "simple_steem_client"],
      install_requires = ["flask", "wtforms"],
      entry_points     = {"console_scripts" : [
                          "tinman=tinman.main:sys_main",
                         ]}
    )

template_source = 'templates'
template_target = '/tmp/tinman-templates'
static_source = 'static'
static_target = '/tmp/tinman-static'

if os.path.exists(template_target):
    shutil.rmtree(template_target)

shutil.copytree(template_source, template_target)

if os.path.exists(static_target):
    shutil.rmtree(static_target)

shutil.copytree(static_source, static_target)
