from setuptools import setup

setup(name="tinman",
      version          = 0.1,
      description      = "Testnet management scripts.",
      url              = "https://github.com/steemit/tinman",
      author           = "Steemit",
      packages         = ["tinman"],
      install_requires = ["steem"],
      scripts          = ["tinman/snapshot.py",
                          "tinman/submit.py",
                          "tinman/txgen.py"])

