from setuptools import setup

setup(name="tinman",
      version=__import__('tinman').__version__,
      description="Testnet management scripts.",
      url="https://github.com/steemit/tinman",
      author= "Steemit",
      packages=["tinman", "simple_steem_client"],
      install_requires=[],
      entry_points={"console_scripts" : [
                          "tinman=tinman.main:sys_main",
                         ]}
      )