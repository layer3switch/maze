# -*- coding: utf-8 -*-
'''
maze game demo behaviors

'''

import os

# Import Python libs
from collections import deque
try:
    import simplejson as json
except ImportError:
    import json

# Import ioflo libs
from ioflo.base.odicting import odict
from ioflo.base.globaling import *

from ioflo.base import aiding
from ioflo.base import storing
from ioflo.base import deeding

from ioflo.base.consoling import getConsole
console = getConsole()

FACINGS = ['north', 'east', 'south', 'west']
HEADINGS = odict([('north', 0), ('east', 90), ('south', 180), ('west', 270)])
OFFSETS = odict([
                ('north', (1, 0)),
                ('east', (0, 1)),
                ('south', (-1, 0)),
                ('west', (0, -1))
                ])

class MazeCommander(deeding.Deed):
    '''
    Manages commander
    '''
    Ioinits = odict(
            inode=".maze.commander",
            server="server",
            commands=odict(ipath=".maze.commands", ival=deque()),
            )

    def postinitio(self):
        '''
        Post process ioinits
        '''
        self.server.value = aiding.SocketUdpNb(host = '', port = 55000, bufsize = 1024)
        self.server.value.reopen()

    def action(self):
        '''
        Update commands from server input
        '''
        server = self.server.value
        commands = self.commands.value
        while True:
            rx, ra = server.receive() #if no data the tuple is ('',None)
            if not rx: # no received data so break
                break
            command = json.loads(rx)
            commands.append(command)
            print "Got: {0}\n".format(command)


@deeding.deedify('MazeCommanderClose', ioinits=odict(
            inode=".maze.commander",
            server="server",))
def commanderclose(self):
    '''
    Close console
    '''
    server = self.server.value
    if server:
        server.close()


class MazeConsoler(deeding.Deed):
    '''
    Manages command console
    '''
    Ioinits = odict(
            inode=".maze.consoler",
            console="console",
            server="server",
            )

    def postinitio(self):
        '''
        Post process ioinits
        '''
        self.console.value = aiding.ConsoleNB()
        self.console.value.open() # open console port
        self.server.value = aiding.SocketUdpNb(host = '', port = 55001, bufsize = 1024)
        self.server.value.reopen()

    def action(self):
        '''
        Update commands from console input
        '''
        console = self.console.value
        server = self.server.value
        while True:
            line = console.getLine()
            if not line:
                break
            chunks = line.lower().split()
            command = None
            if chunks[0].startswith('t'):
                if len(chunks) == 1:
                    value = 'right'
                elif chunks[1].startswith('l'):
                    value = 'left'
                else:
                    value = 'right'
                command = ('turn', value)

            elif chunks[0].startswith('s'):
                command = ('stop', '')

            elif chunks[0].startswith('w'):
                command = ('walk', 1)
            data = json.dumps(command)
            server.send(data, ("127.0.0.1", 55000))
            console.put("Sent: {0}\n".format(command))




@deeding.deedify('MazeConsolerClose', ioinits=odict(
           inode=".maze.consoler",
            console="console",
            server="server", ))
def consolerclose(self):
    '''
    Close console
    '''
    console = self.console.value
    if console:
        console.close()
    if server:
        server.close()



@deeding.deedify('MazeStart', ioinits=odict(
                inode=".maze.",
                onset=odict(ipath="onset", ival=odict(north=0.0, east=0.0)),
                pose=odict(ipath="pose", ival='north'),
                face=odict(ipath="player.face", ival="north"),
                head=odict(ipath="player.head", ival=0.0),
                speed=odict(ipath="player.speed", ival=0),
                position=odict(ipath="player.position", ival=odict(north=0.0, east=0.0)) ))
def mazestart(self, **kwa):
    '''
    Initialize player position,face, and head
    '''
    self.face.value = self.pose.value
    self.head.value = HEADINGS[self.face.value]
    self.speed.value = 0
    self.position.update(north=self.onset.data.north, east=self.onset.data.east)
    print "face='{0}' head={1} speed={2} north={3} east={4}".format(
            self.face.value,
            self.head.value,
            self.speed.value,
            self.position.data.north,
            self.position.data.east, )



class Cell(deeding.Deed):
    '''
    Manages Cell in maze
    '''
    Ioinits = odict(
            inode="framer.me.frame.me.",
            walls=odict(ipath="walls",
                        ival=odict(north=False, east=False, south=False, west=False),
                        iown=True),
            offset=odict(ipath="offset", ival=odict(north=0, east=0), iown=True),
            exited=odict(ipath=".state.exited",
                         ival=odict(north=False, east=False, south=False, west=False)),
            commands=odict(ipath=".maze.commands", ival=deque()),
            face=odict(ipath=".maze.player.face", ival="north"),
            head=odict(ipath=".maze.player.head", ival=0.0),
            view=odict(ipath=".maze.player.view", ival='wall'),
            speed=odict(ipath=".maze.player.speed", ival=0),
            position=odict(ipath=".maze.player.position", ival=odict(north=0.0, east=0.0)),
            )

    def action(self):
        '''
        Update player based on commands
        '''
        for side in self.exited.keys():
            self.exited[side] = False

        self.offset['north'] = 0
        self.offset['east'] = 0

        commands = self.commands.value
        while commands:
            command, value = commands.popleft()
            if command == 'turn':
                if value == 'left':
                    rotation = -1
                else: # value == 'right'
                    rotation = 1
                index = (FACINGS.index(self.face.value) + rotation) % 4
                self.face.value = FACINGS[index]
                self.head.value = HEADINGS[self.face.value]

            elif command == 'stop':
                self.speed.value = 0
            elif command == 'walk':
                # only 1 or zero allowed
                self.speed.value = max(min(int(abs(value)), 1), 0)

        wall = self.walls[self.face.value]
        self.view.value = "wall" if wall else "hall"

        if self.speed.value:
            wall = self.walls[self.face.value]
            if wall:
                self.speed.value = 0
            else:
                dn, de = OFFSETS[self.face.value]
                dn *= self.speed.value
                de *= self.speed.value

                self.position.update(
                        north=int(round(self.position.data.north + dn)),
                        east=int(round(self.position.data.east + de)))

                self.offset.update(
                        north=int(round(self.offset.data.north + dn)),
                        east=int(round(self.offset.data.east + de)))

                self.exited[self.face.value] = True
                self.exited.stampNow()
        print "Player at N{0} E{1} facing {2} sees {3} with speed {4}".format(
                self.position.data.north,
                self.position.data.east,
                self.face.value,
                self.view.value,
                self.speed.value )


class CornerNorthWest(Cell):
    '''
    Manages cell corner on north west
    '''
    Ioinits = odict(
            inode="framer.me.frame.me.",
            walls=odict(ipath="walls",
                        ival=odict(north=True, east=False, south=False, west=True),
                        iown=True),
            offset=odict(ipath="offset", ival=odict(north=0, east=0), iown=True),
            exited=odict(ipath=".state.exited",
                         ival=odict(north=False, east=False, south=False, west=False)),
            commands=odict(ipath=".maze.commands", ival=deque()),
            face=odict(ipath=".maze.player.face", ival="north"),
            head=odict(ipath=".maze.player.head", ival=0.0),
            view=odict(ipath=".maze.player.view", ival='wall'),
            speed=odict(ipath=".maze.player.speed", ival=0),
            position=odict(ipath=".maze.player.position", ival=odict(north=0.0, east=0.0)),
            )

class Corridor(deeding.Deed):
    '''
    Manages Cell in maze
    '''
    Ioinits = odict(
            inode="framer.me.frame.me.",
            size=odict(ipath="size", ival=3, iown=True),
            pose=odict(ipath="pose", ival="north", iown=True),
            bounds=odict(ipath="bounds", ival=odict(north=0, east=0), iown=True),
            walls=odict(ipath="walls",
                        ival=odict(north=False, east=False, south=False, west=False),
                        iown=True),
            offset=odict(ipath="offset", ival=odict(north=0, east=0),
                         iown=True),
            exited=odict(ipath=".state.exited",
                         ival=odict(north=False, east=False, south=False, west=False)),
            commands=odict(ipath=".maze.commands", ival=deque()),
            face=odict(ipath=".maze.player.face", ival="north"),
            head=odict(ipath=".maze.player.head", ival=0.0),
            view=odict(ipath=".maze.player.view", ival='wall'),
            speed=odict(ipath=".maze.player.speed", ival=0),
            position=odict(ipath=".maze.player.position", ival=odict(north=0.0, east=0.0)),
            )

    def postinitio(self):
        '''
        Post process ioinits
        '''
        size = self.size.value
        pose = self.pose.value
        dn, de = OFFSETS[self.pose.value]
        north = max(self.size.value - 1, 0) * dn
        east = max(self.size.value - 1, 0) * de
        self.bounds.update(north=north, east=east)
        if pose in ['north', 'south']:
            self.walls.update(north=False, east=True, south=False, west=True)
        else:
            self.walls.update(north=True, east=False, south=True, west=False)

    def action(self):
        '''
        Update player based on commands
        '''
        size = self.size.value
        pose = self.pose.value
        dn, de = OFFSETS[self.pose.value]
        north = max(self.size.value - 1, 0) * dn
        east = max(self.size.value - 1, 0) * de
        self.bounds.update(north=north, east=east)
        if pose in ['north', 'south']:
            self.walls.update(north=False, east=True, south=False, west=True)
        else:
            self.walls.update(north=True, east=False, south=True, west=False)


        for side in self.exited.keys():
            self.exited[side] = False

        commands = self.commands.value
        while commands:
            command, value = commands.popleft()
            if command == 'turn':
                if value == 'left':
                    rotation = -1
                else: # value == 'right'
                    rotation = 1
                index = (FACINGS.index(self.face.value) + rotation) % 4
                self.face.value = FACINGS[index]
                self.head.value = HEADINGS[self.face.value]

            elif command == 'stop':
                self.speed.value = 0
            elif command == 'walk':
                # only 1 or zero allowed
                self.speed.value = max(min(int(abs(value)), 1), 0)

        wall = self.walls[self.face.value]
        self.view.value = "wall" if wall else "hall"

        if self.speed.value:
            wall = self.walls[self.face.value]
            if wall:
                self.speed.value = 0
            else:

                dn, de = OFFSETS[self.face.value]
                dn *= self.speed.value
                de *= self.speed.value

                self.position.update(
                        north=int(round(self.position.data.north + dn)),
                        east=int(round(self.position.data.east + de)))

                self.offset.update(
                        north=int(round(self.offset.data.north + dn)),
                        east=int(round(self.offset.data.east + de)))

                north = self.offset.data.north
                east = self.offset.data.east

                if north < min(0, self.bounds.data.north):
                    self.exited.update(south=True)
                if north > max(0, self.bounds.data.north):
                    self.exited.update(north=True)
                if east < min(0, self.bounds.data.east):
                    self.exited.update(west=True)
                if east > max(0, self.bounds.data.east):
                    self.exited.update(east=True)

        print "Player at N{0} E{1} facing {2} sees {3} with speed {4}".format(
                self.position.data.north,
                self.position.data.east,
                self.face.value,
                self.view.value,
                self.speed.value )
