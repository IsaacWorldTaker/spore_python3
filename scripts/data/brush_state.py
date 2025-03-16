import math

import maya.cmds as cmds
import maya.OpenMaya as om

import window_utils

class BrushState(object):
    """ object hold the current brush state """


    def __init__(self):
        self.draw = False
        self.position = tuple()
        self.normal = tuple()
        self.tangent = tuple()
        self.last_position = tuple()

        self.target = None
        self._node = None

        self.stroke_direction = tuple()

        self.cursor_x = float()
        self.cursor_y = float()

        self._radius = 1
        self.modify_radius = False
        self.first_scale = True
        self.first_x = float()
        self.last_x = float()

        self.shift_mod = False
        self.meta_mod = False # shift key
        self.ctrl_mod = False # ctrl key

        self.action = None
        self.settings = {}

    @property
    def node(self):
        """ node getter """

        return self._node

    @node.setter
    def node(self, node):
        """ node setter """

        self._node = node
        self._radius = cmds.getAttr('{}.brushRadius'.format(self._node))

    @property
    def radius(self):
        """ brush radius getter """

        return self._radius

    @radius.setter
    def radius(self, radius):
        """ brush radius setter """

        self._radius = radius
        cmds.setAttr('{}.brushRadius'.format(self._node), radius)

    def get_brush_settings(self):
        """ fetch brush setting from the node and save it to the "state" dict """
        # get selected item from node's textScrollList
        sel = cmds.textScrollList('instanceList', q=True, si=True)
        if sel:
            object_index = [int(s.split(' ')[0].strip('[]:')) for s in sel]
        else:
            elements = cmds.textScrollList('instanceList', q=True, ai=True)
            object_index = [int(e.split(' ')[0].strip('[]:')) for e in elements]

        # get modes
        modes = ['place', 'spray', 'scale', 'align', 'move', 'id', 'remove']
        mode_id = cmds.getAttr('{}.contextMode'.format(self._node))
        align_modes = ['normal', 'world', 'object', 'stroke']
        align_id = cmds.getAttr('{}.alignTo'.format(self._node))

        # save state
        self.settings = {'mode': modes[mode_id],
                         'num_samples': cmds.getAttr('{}.numBrushSamples'.format(self._node)),
                         'min_distance': cmds.getAttr('{}.minDistance'.format(self._node)),
                         'fall_off': cmds.getAttr('{}.fallOff'.format(self._node)),
                         'align_to': align_modes[align_id],
                         'strength': cmds.getAttr('{}.strength'.format(self._node)),
                         'min_rot': cmds.getAttr('{}.minRotation'.format(self._node))[0],
                         'max_rot': cmds.getAttr('{}.maxRotation'.format(self._node))[0],
                         'uni_scale': cmds.getAttr('{}.uniformScale'.format(self._node)),
                         'min_scale': cmds.getAttr('{}.minScale'.format(self._node))[0],
                         'max_scale': cmds.getAttr('{}.maxScale'.format(self._node))[0],
                         'scale_factor': cmds.getAttr('{}.scaleFactor'.format(self._node)),
                         'scale_amount': cmds.getAttr('{}.scaleAmount'.format(self._node)),
                         'min_offset': cmds.getAttr('{}.minOffset'.format(self._node)),
                         'max_offset': cmds.getAttr('{}.maxOffset'.format(self._node)),
                         'ids': object_index}

        self.radius = cmds.getAttr('{}.brushRadius'.format(self._node))


    def get_screen_position(self, invert_y=True):
        """ get the current brush position in screen space coordinates
        :param invert_y: inverts the y to convert maya coords to qt coords
                         qt = True, maya = False
        :return: x, y position if draw is True else: None"""

        if self.draw:
            view = window_utils.active_view()
            point = om.MPoint(self.position[0], self.position[1], self.position[2])

            x_util = om.MScriptUtil()
            x_ptr = x_util.asShortPtr()
            y_util = om.MScriptUtil()
            y_ptr = y_util.asShortPtr()
            view.worldToView(point, x_ptr, y_ptr)
            x_pos = x_util.getShort(x_ptr)
            y_pos = y_util.getShort(y_ptr)

            if invert_y:
                y_pos = view.portHeight() - y_pos

            return x_pos, y_pos

        else:
            return None


    def create_brush_shape(self):

        if self.draw:
            # fetch point and normal
            pnt = om.MPoint(self.position[0],
                            self.position[1],
                            self.position[2])
            nrm = om.MVector(self.normal[0],
                            self.normal[1],
                            self.normal[2])
            tan = om.MVector(self.tangent[0],
                            self.tangent[1],
                            self.tangent[2])

            # draw dragger shapes
            if self.shift_mod:
                pos_x, pos_y = self.world_to_view(pnt)

                shapes = []
                shapes.append([(pos_x - 15, pos_y - 15), (pos_x + 15, pos_y + 15)])
                shapes.append([(pos_x - 15, pos_y + 15), (pos_x + 15, pos_y - 15)])
                return shapes


            else:
                # get point at normal and tangent
                #  n_pnt = pnt + (nrm * self._state.radius * 0.75)
                #  t_str = pnt + (tan * self._state.radius * 0.75)
                #  t_end = pnt + (tan * self._state.radius)

                # get circle points
                theta = math.radians(360 / 20)
                shape = []
                for i in range(20 + 1):
                    rot = om.MQuaternion(theta * i, nrm)
                    rtan = tan.rotateBy(rot)
                    pos = pnt + (rtan * self._radius)

                    pos_x, pos_y = self.world_to_view(pos)
                    shape.append((pos_x, pos_y))

                return [shape]

    def world_to_view(self, position, invert_y=True):
        """ convert the given 3d position to 2d viewport coordinates
        :param invert_y bool: convert between qt and maya coordinate space """

        view = window_utils.active_view()
        x_util = om.MScriptUtil()
        y_util = om.MScriptUtil()

        x_ptr = x_util.asShortPtr()
        y_ptr = y_util.asShortPtr()
        view.worldToView(position, x_ptr, y_ptr)
        x_pos = x_util.getShort(x_ptr)
        y_pos = y_util.getShort(y_ptr)

        if invert_y:
            y_pos = view.portHeight() - y_pos

        return (x_pos, y_pos)

    def __str__(self):
        return self
