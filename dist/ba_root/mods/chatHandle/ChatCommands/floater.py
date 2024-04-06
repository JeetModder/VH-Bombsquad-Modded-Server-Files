# ba_meta require api 6
from __future__ import annotations
from typing import TYPE_CHECKING
import ba, _ba
import random
import math
from bastd.gameutils import SharedObjects
from bastd.actor.bomb import Bomb
from ba._generated.enums import InputType

if TYPE_CHECKING:
    from typing import Optional

class Floater(ba.Actor):
    def __init__(self, bounds: tuple):
        super().__init__()
        shared = SharedObjects.get()
        self.controlled = False
        self.source_player = None
        self.floater_material = ba.Material()
        self.floater_material.add_actions(
            conditions=('they_have_material',
                        shared.player_material),
            actions=(('modify_node_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True)))
        self.floater_material.add_actions(
            conditions=(('they_have_material',
                         shared.object_material), 'or',
                        ('they_have_material',
                         shared.footing_material), 'or',
                        ('they_have_material',
                         self.floater_material)),
            actions=('modify_part_collision', 'physical', False))

        self.pos = bounds
        self.px = random.uniform(self.pos[0], self.pos[3])
        self.py = random.uniform(self.pos[1], self.pos[4])
        self.pz = random.uniform(self.pos[2], self.pos[5])

        self.node = ba.newnode(
            'prop',
            delegate=self,
            owner=None,
            attrs={
                'position': (self.px, self.py, self.pz),
                'model': ba.getmodel('landMine'),
                'light_model': ba.getmodel('landMine'),
                'body': 'landMine',
                'body_scale': 3,
                'model_scale': 3.1,
                'shadow_size': 0.25,
                'density': 999999,
                'gravity_scale': 0.0,
                'color_texture': ba.gettexture('achievementFlawlessVictory'),
                'reflection': 'soft',
                'reflection_scale': [0.25],
                'materials': [shared.footing_material, self.floater_material]
            })
        self.node2 = ba.newnode(
            'prop',
            owner=self.node,
            attrs={
                'position': (0, 0, 0),
                'body': 'sphere',
                'model': None,
                'color_texture': None,
                'body_scale': 1.0,
                'reflection': 'powerup',
                'density': 999999,
                'reflection_scale': [1.0],
                'model_scale': 1.0,
                'gravity_scale': 0,
                'shadow_size': 0.1,
                'is_area_of_interest': True,
                'materials': [shared.object_material, self.floater_material]
            })
        self.node.connectattr('position', self.node2, 'position')

    def check_can_control(self) -> bool:
        if not self.node.exists():
            return False
        if not self.source_player.is_alive():
            self.dis()
            return False
        return True

    def con(self) -> None:
        self.controlled = True
        self.check_player_die()

    def up(self) -> None:
        if not self.check_can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], 5, v[2])

    def upR(self) -> None:
        if not self.check_can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], 0, v[2])

    def down(self) -> None:
        if not self.check_can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], -5, v[2])

    def downR(self) -> None:
        if not self.check_can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], 0, v[2])

    def leftright(self, value: float) -> None:
        if not self.check_can_control():
            return
        v = self.node.velocity
        self.node.velocity = (5 * value, v[1], v[2])

    def updown(self, value: float) -> None:
        if not self.check_can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], v[1], -5 * value)

    def dis(self) -> None:
        if self.node.exists():
            self.controlled = False
            self.node.velocity = (0, 0, 0)
            self.move()

    def check_player_die(self) -> None:
        if not self.controlled:
            return
        if self.source_player is None:
            return
        if self.source_player.is_alive():
            ba.timer(1, self.check_player_die)
            return
        else:
            self.dis()

    def distance(self, x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> float:
        d = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2) + math.pow(z2 - z1, 2))
        return d

    def drop(self) -> None:
        try:
            np = self.node.position
        except:
            np = (0, 0, 0)
        self.b = Bomb(bomb_type=random.choice(['normal', 'ice', 'sticky', 'impact', 'land_mine', 'tnt']),
                      source_player=self.source_player, position=(np[0], np[1] - 1, np[2]), velocity=(0, -1, 0)).autoretain()
        if self.b.bomb_type in ['impact', 'land_mine']:
            self.b.arm()

    def move(self) -> None:
        px = self.px
        py = self.py
        pz = self.pz
        if self.node.exists() and not self.controlled:
            pn = self.node.position
            dist = self.distance(pn[0], pn[1], pn[2], px, py, pz)
            self.node.velocity = ((px - pn[0]) / dist, (py - pn[1]) / dist, (pz - pn[2]) / dist)
            t = dist - 1 if dist - 1 >= 0 else 0.1
            ba.timer(t, ba.WeakCall(self.move), suppress_format_warning=True)

    def handlemessage(self, msg) -> None:
        if isinstance(msg, ba.DieMessage):
            self.node.delete()
            self.node2.delete()
            self.controlled = False
        elif isinstance(msg, ba.OutOfBoundsMessage):
            self.handlemessage(ba.DieMessage())
        else:
            super().handlemessage(msg)

def assign_flo_inputs(client_id: int) -> None:
    with ba.Context(_ba.get_foreground_host_activity()):
        activity = ba.getactivity()
        # Check if the activity is a type that has a 'map' attribute
        if not hasattr(activity, 'flo') or not activity.flo.node.exists():
            try:
                activity.flo = Floater(activity.map.get_def_bound_box('map_bounds'))
            except Exception as e:
                print(f"An error occurred while creating Floater: {e}")
                return  # Perhaps using in main-menu/score-screen
        else:
            # Reset the controlled flag to allow control again
            activity.flo.controlled = False

        floater = activity.flo
        if floater.controlled:
            ba.screenmessage('Floater is already being controlled', color=(1, 0, 0), transient=True, clients=[client_id])
            return
        ba.screenmessage('You Gained Control Over The Floater!\n Press Bomb to Throw Bombs and Punch to leave!', clients=[client_id], transient=True, color=(0, 1, 1))
        for i in _ba.get_foreground_host_activity().players:
            if i.sessionplayer.inputdevice.client_id == client_id:
                def dis(i, floater):
                    i.actor.node.invincible = False
                    i.resetinput()
                    i.actor.connect_controls_to_player()
                    floater.dis()
                ps = i.actor.node.position
                i.actor.node.invincible = True
                floater.node.position = (ps[0], ps[1] + 1.0, ps[2])
                i.actor.node.hold_node = ba.Node(None)
                i.actor.node.hold_node = floater.node2
                i.actor.connect_controls_to_player()
                i.actor.disconnect_controls_from_player()
                i.resetinput()
                floater.source_player = i
                floater.con()
                i.assigninput(InputType.PICK_UP_PRESS, floater.up)
                i.assigninput(InputType.PICK_UP_RELEASE, floater.upR)
                i.assigninput(InputType.JUMP_PRESS, floater.down)
                i.assigninput(InputType.BOMB_PRESS, floater.drop)
                i.assigninput(InputType.PUNCH_PRESS, ba.Call(dis, i, floater))
                i.assigninput(InputType.UP_DOWN, floater.updown)
                i.assigninput(InputType.LEFT_RIGHT, floater.leftright)
