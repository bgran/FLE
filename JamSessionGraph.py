# $Id: JamSessionGraph.py,v 1.3 2003/06/13 07:57:11 jmp Exp $

# Copyright 2001, 2002, 2003 by Fle3 Team and contributors
#
# This file is part of Fle3.
#
# Fle3 is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Fle3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fle3; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Contains classes LayeredGraph and JamSessionGraph."""

__version__ = '$Revision: 1.3 $'[11:-2]

try:
    from PIL import Image, ImageDraw
except ImportError:
    pass
import cStringIO
import Globals
from AccessControl import ClassSecurityInfo
from JamSession import JamSession
from common import perm_view, perm_edit, perm_manage, perm_add_lo

# The sole purpose of this class is to help JamSessionGraph.
# The code does not probably make too much sense unless you know something
# about graph drawing. The information used to implement this class comes
# from the book "Graph Drawing: Algorithms for the Visualization of Graphs"
class LayeredGraph:
    """This class helps to draw DAG as a layered graph."""

    def __init__(self, V, E):

        destination_nodes = []
        for (u,v) in E:
            destination_nodes.append(v)

        self.__nodes = {}
        for node in V:
            self.__nodes[node] = {}

        for node in V:
            if node not in destination_nodes:
                self.__start_node = node
                break

        self.__edges = E

        self.__to_layered_graph()
        self.__to_proper()
        self.__reduce_crossings()

    def get_representation(self):
        G = {}
        G['nodes'] = self.__nodes
        G['edges'] = self.__edges
        G['layers'] = self.__layers
        return G

    def __to_layered_graph(self):
        nodes = self.__nodes
        edges = self.__edges

        # At this point every node is real, i.e. there are not dummy nodes.
        done = []
        todo = []
        for node_name in nodes.keys():
            nodes[node_name]['real'] = 1
            if node_name == self.__start_node:
                nodes[node_name]['layer'] = 0
                done.append(node_name)
            else:
                nodes[node_name]['layer'] = -1
                todo.append(node_name)

        # Assign nodes to layers.
        while len(todo) > 0:
            for (u,v) in edges:
                if (u not in done) or (v not in todo):
                    continue

                # Node u is assigned to some layer.
                # Node v does not has layer yet.

                # We can assign a layer to v, if for all (x,v) in
                # edges, node x already has an assigned layer...
                ok = 1
                u_nodes = []
                for (a,b) in edges:
                    if b is not v: continue
                    if a not in done:
                        ok = 0
                        break
                    else:
                        u_nodes.append(a)

                # ... no, that is not the case.
                if not ok:
                    continue

                # Yes, we can assign a layer to v.
                layer = max([nodes[n]['layer'] for n in u_nodes])
                nodes[v]['layer'] = layer + 1
                done.append(v)
                todo.remove(v)

    def __to_proper(self):
        nodes = self.__nodes
        edges = self.__edges
        # Make dummy nodes
        i = 0
        to_remove = []
        for (u,v) in edges:
            difference = nodes[v]['layer'] - nodes[u]['layer']

            # All egdes that span several layers are replaced with
            # dummy layers and short edges, e.g:
            #
            # layer 0   N                N
            #           |\               |\
            # layer 1   N |              N D
            #           | |     ==>      | |
            # layer 2   N |              N D
            #             |                |
            # layer 3     N                N
            #
            # N = node, D = dummy node

            if difference > 1:
                to_remove.append((u,v)) # remove the original edge later

                layer = nodes[u]['layer'] + 1
                a = u
                while difference > 1:
                    b = 'dummy' + str(i)

                    # make edge
                    edges.append((a,b))

                    # make dummy node
                    dummy_node = {'layer': layer, 'real': 0}
                    nodes[b] = dummy_node

                    # update for next loop
                    a = b; i += 1; difference -= 1; layer +=1

                edges.append((b,v)) # the edge from the last dummy node

        # Actual removing
        for (u,v) in to_remove:
            edges.remove((u,v))

        # Order of nodes on each layer. (Cross reduction phase
        # will re-order nodes on each layer...)
        layers = []
        for i in range(0, max([nodes[node_name]['layer'] for \
                               node_name in nodes.keys()]) + 1):
            layers.append([])
        for node_name in nodes.keys():
            l = nodes[node_name]['layer']
            layers[l].append(node_name)

        self.__layers = layers


    def __n_crossings(self):
        n = 0
        for i in range(1, len(self.__layers)):
            n += self.__crossing_number(i-1, i)
        return n

    def __crossing_number(self, layer_1_index, layer_2_index):
        if layer_1_index > layer_2_index:
            layer_1_index, layer_2_index = layer_2_index, layer_1_index

        layer_1 = self.__layers[layer_1_index]
        layer_2 = self.__layers[layer_2_index]
        number = 0
        for u in range(0, len(layer_2)):
            for v in range(u+1, len(layer_2)):
                u_pos = []
                v_pos = []
                for (a,b) in self.__edges:
                    if (a not in layer_1) or (b not in layer_2): continue
                    if b == layer_2[u]:
                        u_pos.append(layer_1.index(a))
                    elif b == layer_2[v]:
                        v_pos.append(layer_1.index(a))
                for i in v_pos:
                    for j in u_pos:
                        if j > i: number += 1
        return number

    # Median method (not perfect, odd and even degree stuff is
    # not implemented.)
    def __two_layer_crossing_reduce(self,
                                    fixed_layer_index,
                                    changing_layer_index):
        nodes = self.__nodes
        layers = self.__layers
        fixed_layer = layers[fixed_layer_index]
        changing_layer = layers[changing_layer_index]

        pos = []
        for node_name in changing_layer:
            neighbour_pos = []
            for neighbour in nodes[node_name]['neighbours']:
                if nodes[neighbour]['layer'] != fixed_layer_index: continue
                neighbour_pos.append(fixed_layer.index(neighbour))

            if len(neighbour_pos) > 0:
                pos.append(neighbour_pos[len(neighbour_pos)/2])
            else:
                pos.append(0)

        for j in range(0, len(pos)):
            min_val = pow(2,30)
            index = 0
            for k in range(0, len(pos)):
                if pos[k] >= 0 and pos[k] < min_val:
                    min_val = pos[k]
                    index = k

            pos[index] = -len(pos) + j

        for j in range(0,len(pos)):
            pos[j] += len(pos)

        new_layer = []
        for j in range(len(changing_layer)):
            new_layer.append(changing_layer[pos[j]])

        layers[changing_layer_index] = new_layer

    def __reduce_crossings(self):
        nodes = self.__nodes
        edges = self.__edges

        # Add explicit neigbourhood information to each node
        for node_name in nodes.keys():
            nodes[node_name]['neighbours'] = []
        for (u,v) in edges:
            u_neighbours = nodes[u]['neighbours']
            v_neighbours = nodes[v]['neighbours']
            if v not in u_neighbours:
                u_neighbours.append(v)
            if u not in v_neighbours:
                v_neighbours.append(u)


        # Crossing reduction

        r = range(1, len(self.__layers))

        n_a = 0 # number of crossing after top to bottom sweep
        n_b = 0 # number of crossing after bottom to top sweep
        n_loops = 0
        tested = []
        min_val = pow(2,30)

        while n_loops < 10 and ((n_a, n_b) not in tested or n_b > min_val):
            n_loops += 1
            tested.append((n_a, n_b))

            # sweep from top to bottom...
            for i in r: self.__two_layer_crossing_reduce(i-1, i)
            n_a = self.__n_crossings()
            r.reverse()

            # ... and back from bottom to top.
            for i in r:  self.__two_layer_crossing_reduce(i, i-1)
            n_b = self.__n_crossings()
            r.reverse()

            if n_b < min_val:
                min_val = n_b

class JamSessionGraph(JamSession):
    """JamSessionGraph"""

    meta_type = 'JamSession'
    security= ClassSecurityInfo()
    security.declareObjectPublic()

    security.declareProtected(perm_view, 'get_type')
    def get_type(self):
        """Return type of the JamSession."""
        return 'graph'

    security.declareProtected(perm_view, 'get_printable_type')
    def get_printable_type(self, REQUEST):
        """Return printable (localized) type of the JamSession."""
        return REQUEST['L_diverge_and_converge']

    security.declarePrivate('update_drawing')
    def update_drawing(self):
        G = self.build_graph().get_representation()

        # Assign horizontal positions for nodes ( real and dummy ones)
        # FIXME: This code just puts nodes next to each other starting
        # FIXME: from left.
        columns = []
        max_width = 0
        for layer in G['layers']:
            width = 0
            cols = 0
            for node_name in layer:
                node = G['nodes'][node_name]
                if node['real'] == 1:
                    node['position'] = width + 30 + 60
                    width += 5 * 30
                else:
                    node['position'] = width + 15
                    width += 30

            if width > max_width: max_width = width

            columns.append(width / 30)

        # How much we have to pad each (layer) row of the table?
        for i in range(0, len(G['layers'])):
            columns[i] = max_width/30 - columns[i]

        G['width'] = max_width
        G['columns'] = columns
        G['n_nodes'] = n_nodes = len(
            filter(lambda key, G=G: \
                   G['nodes'][key]['real'] == 1, G['nodes'].keys()))

        # Delete old images.
        self.manage_delObjects(self.objectIds('Image'))

        # Draw new ones.
        for i in range(1, len(G['layers'])):
            im = Image.new('L', (max_width, 40), 255)
            draw = ImageDraw.Draw(im)

            for node_name in G['layers'][i]:

                # If one node has several parent nodes, we want that
                # incoming edges are separated:
                #
                #   BAD!         GOOD!
                #
                #   \ | /     \    |    /
                #    \|/       \   |   /
                #  **node**     **node**
                #
                # Therefore, we put edges to the dictionary so that
                # we can handle one node at a time.
                to_draw = {}
                for (u,v) in G['edges']:
                    if v == node_name:
                        if to_draw.has_key(v):
                            to_draw[v].append(u)
                        else:
                            to_draw[v]=[u]

                # Loop over nodes
                for v in to_draw.keys():

                    # Sort edges (u,v) by x-coordinate of u node...
                    data = []
                    for u in to_draw[v]:
                        data.append( (u, v, G['nodes'][u]['position']) )
                    data.sort(lambda x,y: ((x[2] <= y[2]) and [-1] or [1])[0])

                    # .. and then draw them from left to right
                    delta_delta = min(10, 100 / len(data))
                    delta = ((len(data)-1) / 2) * -delta_delta
                    for (u,v, dummy) in data:
                        draw.line([(G['nodes'][u]['position'], 0),
                                   (G['nodes'][v]['position']+delta, 30),
                                   (G['nodes'][v]['position']+delta, 40)],
                                  fill=0)

                        # Draw arrow?
                        if G['nodes'][v]['real'] == 1:
                            draw.line([(G['nodes'][v]['position']+delta, 39),
                                       (G['nodes'][v]['position']+delta-4,35)],
                                      fill=0)
                            draw.line([(G['nodes'][v]['position']+delta, 39),
                                       (G['nodes'][v]['position']+delta+4,35)],
                                      fill=0)

                        delta += delta_delta

            del draw
            s = cStringIO.StringIO()
            im.save(s, 'GIF')
            s.seek(0)
            content = s.read()
            name = 'layer_' + str(i) + '_' + str(n_nodes)
            self.manage_addImage(name, content, '')

        self.drawing = G


    security.declarePrivate('build_graph')
    def build_graph(self):
        V = []
        E = []
        for ja in self.get_children('JamArtefact'):
            v = ja.get_id()
            V.append(v)
            for u in ja.get_parent_ids():
                E.append((u,v))

        return LayeredGraph(V, E)

Globals.default__class_init__(JamSessionGraph)
