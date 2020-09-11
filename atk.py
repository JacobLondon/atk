import copy
import json
import math
import random
import time
from typing import List

from pyngine import *
from pyfs import filesystem

with open("settings.json", "r") as s:
    settings = json.load(s)

client = filesystem.FileSystemUDPClient(settings["ip"], settings["port"])
now = time.time()

ID_GOOD = 0
ID_BAD = 1

SHOOT_1 = 0
SHOOT_2 = 1
SHOOT_3 = 2
SHOOT_SIDES = 3
SHOOT_STAR = 4
SHOOT_SPIRAL = 5
SHOOT_COUNT = 6

UP = -1
DOWN = 1
SHOT_VELOCITY = 10
SHOT_SIZE = 10
SHOT_COOLDOWN = 0.1

ENEMY_COOLDOWN = 0.5
ENEMY_SIZE = 30
PLAYER_SIZE = 50
PLAYER_HEALTH = 100

ENEMY_VELOCITY = 3

MOVEMENT_NONE = 0   # standstill
MOVEMENT_NORMAL = 1 # move down slowly
MOVEMENT_WEAVE = 2  # sin wave
MOVEMENT_LEFT = 3 # linear across and down
MOVEMENT_RIGHT = 4
movement_name = {
    MOVEMENT_NONE:   "Move: 1 - None",
    MOVEMENT_NORMAL: "Move: 2 - Normal",
    MOVEMENT_WEAVE:  "Move: 3 - Weave",
    MOVEMENT_LEFT:   "Move: 4 - Left",
    MOVEMENT_RIGHT:  "Move: 5 - Right",
}
movement_lookup = {
    MOVEMENT_NONE: (lambda   x, y: (x, y)),
    MOVEMENT_NORMAL: (lambda x, y: (x, y + ENEMY_VELOCITY)),
    MOVEMENT_WEAVE: (lambda  x, y: (x + math.sin(now * math.pi) * 5, y + ENEMY_VELOCITY)),
    MOVEMENT_LEFT: (lambda   x, y: (x - ENEMY_VELOCITY, y + ENEMY_VELOCITY)),
    MOVEMENT_RIGHT: (lambda  x, y: (x + ENEMY_VELOCITY, y + ENEMY_VELOCITY)),
}

def getmove(m, x, y):
    return movement_lookup[m](x, y)

class Creature:
    def __init__(self):
        pass
    def update(self):
        pass
    def draw(self):
        pass
    def serialize(self):
        return self.__dict__

class Shot:
    def __init__(self, x: int, y: int, d: int, dx: int):
        self.x = x
        self.y = y
        self.d = d # UP or DOWN
        self.dx = dx # how much the x moves

    def update(self):
        self.y += self.d * SHOT_VELOCITY
        self.x += self.dx * SHOT_VELOCITY

    def serialize(self):
        return self.__dict__

# enemies only
atk_lookup = [None for _ in range(SHOOT_COUNT)]
atk_lookup[SHOOT_1]      = lambda x, y: [Shot(x, y, DOWN, 0)]
atk_lookup[SHOOT_2]      = lambda x, y: [Shot(x, y, DOWN, 1), Shot(x, y, DOWN, -1)]
atk_lookup[SHOOT_3]      = lambda x, y: [Shot(x, y, DOWN, 0), Shot(x, y, DOWN, 1), Shot(x, y, DOWN, -1)]
atk_lookup[SHOOT_SIDES]  = lambda x, y: [Shot(x, y, 0, 1), Shot(x, y, 0, -1)]
atk_lookup[SHOOT_STAR]   = lambda x, y: [
    Shot(x, y, UP, 0), Shot(x, y, UP, 1), Shot(x, y, UP, -1),
    Shot(x, y, 0, 1), Shot(x, y, 0, -1),
    Shot(x, y, DOWN, 0), Shot(x, y, DOWN, 1), Shot(x, y, DOWN, -1)
]
atk_lookup[SHOOT_SPIRAL] = lambda x, y: [Shot(x, y, math.sin(now * math.pi), math.cos(now * math.pi))]

atk_name = {
    SHOOT_1:      "Shot: Q - Single",
    SHOOT_2:      "Shot: W - Double",
    SHOOT_3:      "Shot: E - Triple",
    SHOOT_SIDES:  "Shot: R - Sides",
    SHOOT_STAR:   "Shot: T - Star",
    SHOOT_SPIRAL: "Shot: Y - Spiral",
}

def getatk(id, x, y):
    # just assume id is in range... return the shot list
    return atk_lookup[id](x, y)

class Game(Controller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        this = self

        # this is owned by the server
        self.players = []
        self.uid = random.randint(0, 100_000)

        class Good(Creature):
            def __init__(self):
                self.uid = this.uid
                self.id = ID_GOOD
                self.x = this.screen_width / 2
                self.y = this.screen_height - 100
                self.hp = PLAYER_HEALTH
                self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                self.shoot = SHOOT_3
                self.shots: List[Shot] = []
                self.cooldown = now

                self.hp_label = Label(this, str(self.hp))
                Event(this, self.newshot, keys=(pg.K_SPACE,))

            def newshot(self):
                if now < self.cooldown + SHOT_COOLDOWN:
                    return

                self.cooldown = now
                if self.shoot == SHOOT_1:
                    self.shots.append(Shot(self.x, self.y, UP, 0))
                elif self.shoot == SHOOT_2:
                    self.shots.append(Shot(self.x, self.y, UP, 1))
                    self.shots.append(Shot(self.x, self.y, UP, -1))
                else:
                    self.shots.append(Shot(self.x, self.y, UP, 0))
                    self.shots.append(Shot(self.x, self.y, UP, 1))
                    self.shots.append(Shot(self.x, self.y, UP, -1))

            def update(self):
                self.hp_label.text = str(self.hp)
                self.x = this.mouse.x
                self.y = this.mouse.y

                for shot in self.shots:
                    shot.update()

                # do damage check, even tho square, hitboxes are circles
                for player in this.players:
                    if player.id == ID_BAD:
                        for minion in player.minions:
                            for shot in minion.shots:
                                if abs(self.x - shot.x) < PLAYER_SIZE / 2:
                                    self.hp -= 1

                # clear off screen
                self.shots = list(filter(lambda shot: 0 <= shot.x <= this.screen_width and 0 <= shot.y <= this.screen_height, self.shots))

            def draw(self):
                this.painter.fill_rect(self.x - PLAYER_SIZE / 2, self.y - PLAYER_SIZE / 2, PLAYER_SIZE, PLAYER_SIZE, self.color)

                for shot in self.shots:
                    this.painter.fill_rect(shot.x - SHOT_SIZE / 2, shot.y - SHOT_SIZE / 2, SHOT_SIZE, SHOT_SIZE, self.color)

            def serialize(self):
                return {
                    "uid": self.uid,
                    "id": self.id,
                    "x": self.x,
                    "y": self.y,
                    "hp": self.hp,
                    "color": self.color,
                    "shots": [shot.serialize() for shot in self.shots],
                }

        class Enemy(Creature):
            def __init__(self, x: int, y: int, m: int, id: int):
                self.x = x
                self.y = y
                self.m = m # movement pattern id
                self.id = id # shot id
                self.shots = []
                self.hp = 5
                self.color = Color['crimson']
                self.cooldown = now

            def update(self):
                # do damage check, even tho square, hitboxes are circles
                for player in this.players:
                    if player.id == ID_GOOD:
                        for shot in player.shots:
                            if abs(self.x - shot.x) < ENEMY_SIZE / 2:
                                self.hp -= 1

                self.x, self.y = getmove(self.m, self.x, self.y)

                if now > self.cooldown + ENEMY_COOLDOWN:
                    self.shots.extend(getatk(self.id, self.x, self.y))
                    self.cooldown = now
                
                for shot in self.shots:
                    shot.update()

                self.shots = list(filter(lambda shot: 0 <= shot.x <= this.screen_width and 0 <= shot.y <= this.screen_height, self.shots))

            def draw(self):
                this.painter.fill_rect(self.x - ENEMY_SIZE / 2, self.y - ENEMY_SIZE / 2, ENEMY_SIZE, ENEMY_SIZE, (255, 0, 0))
                for shot in self.shots:
                    this.painter.fill_rect(shot.x - SHOT_SIZE / 2, shot.y - SHOT_SIZE / 2, SHOT_SIZE, SHOT_SIZE, (255, 0, 0))

            def serialize(self):
                return {
                    "x": self.x,
                    "y": self.y,
                    "m": self.m,
                    "shots": [shot.serialize() for shot in self.shots],
                    "hp": self.hp
                }

        class Bad(Creature):
            def __init__(self):
                self.uid = this.uid
                self.id = ID_BAD
                self.hp = 100
                self.minions: Enemy = []
                self.spawntype = MOVEMENT_NORMAL
                self.shottype = SHOOT_1
                self.text = movement_name[self.spawntype]
                self.shottext = atk_name[self.shottype]
                self.cooldown = now

                self.hp_label = Label(this, str(self.hp), z=9999)
                self.spawn_label = Label(this, self.text, z=10000)
                self.spawn_label.loc = (0, 15)
                self.shot_label = Label(this, self.shottext, z=10001)
                self.shot_label.loc = (0, 30)

                Event(this, self.newemeny, keys=(pg.K_SPACE,))

                Event(this, self.set_none,   keys=(pg.K_1))
                Event(this, self.set_normal, keys=(pg.K_2))
                Event(this, self.set_weave,  keys=(pg.K_3))
                Event(this, self.set_left,   keys=(pg.K_4))
                Event(this, self.set_right,  keys=(pg.K_5))

                Event(this, self.shot_1,      keys=(pg.K_q,))
                Event(this, self.shot_2,      keys=(pg.K_w,))
                Event(this, self.shot_3,      keys=(pg.K_e,))
                Event(this, self.shot_sides,  keys=(pg.K_r,))
                Event(this, self.shot_star,   keys=(pg.K_t,))
                Event(this, self.shot_spiral, keys=(pg.K_y,))

            def newemeny(self):
                if time.time() < self.cooldown + ENEMY_COOLDOWN:
                    return

                if this.mouse.y > this.screen_height / 2:
                    return

                self.cooldown = now
                self.minions.append(Enemy(this.mouse.x, this.mouse.y, self.spawntype, self.shottype))

            def shot_1(self):
                self.shottype = SHOOT_1
                self.shottext = atk_name[self.shottype]

            def shot_2(self):
                self.shottype = SHOOT_2
                self.shottext = atk_name[self.shottype]

            def shot_3(self):
                self.shottype = SHOOT_3
                self.shottext = atk_name[self.shottype]

            def shot_sides(self):
                self.shottype = SHOOT_SIDES
                self.shottext = atk_name[self.shottype]

            def shot_star(self):
                self.shottype = SHOOT_STAR
                self.shottext = atk_name[self.shottype]

            def shot_spiral(self):
                self.shottype = SHOOT_SPIRAL
                self.shottext = atk_name[self.shottype]

            def set_none(self):
                self.spawntype = MOVEMENT_NONE
                self.text = movement_name[self.spawntype]
            
            def set_normal(self):
                self.spawntype = MOVEMENT_NORMAL
                self.text = movement_name[self.spawntype]
            
            def set_weave(self):
                self.spawntype = MOVEMENT_WEAVE
                self.text = movement_name[self.spawntype]
            
            def set_left(self):
                self.spawntype = MOVEMENT_LEFT
                self.text = movement_name[self.spawntype]

            def set_right(self):
                self.spawntype = MOVEMENT_RIGHT
                self.text = movement_name[self.spawntype]

            def update(self):
                self.hp_label.text = str(self.hp)
                self.spawn_label.text = self.text
                self.shot_label.text = self.shottext

                for minion in self.minions:
                    minion.update()
                    if minion.hp <= 0:
                        self.hp -= 1

                self.minions = list(filter(
                    lambda minion: 0 <= minion.x <= this.screen_width \
                        and 0 < minion.y <= this.screen_height \
                        and minion.hp > 0, self.minions))

            def draw(self):
                for minion in self.minions:
                    minion.draw()

            def serialize(self):
                return {
                    "uid": self.uid,
                    "id": self.id,
                    "hp": self.hp,
                    "minions": [minion.serialize() for minion in self.minions],
                }

        # just assume the user has a unique name lol
        self.player: Creature
        if settings["player"]["type"].lower() == "good":
            self.player = Good()
        else:
            self.player = Bad()

        Event(self, self.exit_program, keys=(pg.K_ESCAPE,))
        Drawer(self, self.move)

    def serialize(self):
        return self.__dict__

    def send(self):
        pass

    def read(self):
        pass

    def move(self):
        global now
        now = time.time()

        self.player.update()
        if self.player.hp > 0:
            self.player.draw()

        # we don't own just update
        for player in self.players:
            if player.uid != self.player.uid:
                player.update()
                player.draw()

if __name__ == '__main__':
    game = Game(name="Atk", resolution=(600, 720), grid=(80, 60), debug=False)
    game.run()
