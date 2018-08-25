#!/usr/bin/env python3

import collections
import sys

from . import snapshot
from . import txgen
from . import gatling
from . import keysub
from . import sample
from . import submit
from . import warden
from . import amountsub

class Help(object):

    @staticmethod
    def main(argv):
        print("Available commands:")
        for k, v in commands.items():
            print("   "+k)
        print("argv:", argv)
        return

commands = collections.OrderedDict((
            ("snapshot", snapshot),
            ("txgen"   , txgen   ),
            ("gatling" , gatling ),
            ("keysub"  , keysub  ),
            ("sample"  , sample  ),
            ("submit"  , submit  ),
            ("warden"  , warden  ),
            ("amountsub"  , amountsub  ),
            ("help"    , Help    ),
           ))

def main(argv):
    if len(argv) == 0:
        argv = list(argv) + ["tinman"]
    if len(argv) == 1:
        argv = list(argv) + ["--help"]
    module_name = argv[1]
    if module_name == "--help":
        module_name = "help"
    module = commands.get(module_name)
    if module is None:
        print("no module specified, executing help")
        Help.main([])
        return 1
    return module.main(argv[1:])

def sys_main():
    result = main(sys.argv)
    if result is None:
        result = 0
    sys.exit(result)

if __name__ == "__main__":
    sys_main()
