#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ioflo CLI

Runs ioflo plan from command line shell

example:

mazeflo -v verbose -n maze -p 0.0625 -f maze/maze.flo -b maze


"""
import sys
import ioflo.app.run

def main():
    """ Main entry point for ioflo CLI"""
    args = ioflo.app.run.parseArgs()

    if args.version:
        print "ioflo version {0}".format(ioflo.__version__)
        sys.exit(0)

    ioflo.app.run.run(  name=args.name,
                        filepath = args.filename,
                        period = float(args.period),
                        verbose = args.verbose,
                        real = args.realtime,
                        behaviors=args.behaviors,
                        username=args.username,
                        password=args.password, )

if __name__ == '__main__':
    main()

