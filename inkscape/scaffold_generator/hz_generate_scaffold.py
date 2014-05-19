#!/usr/bin/env python2
'''
Copyright (C) 2007 Martin Owens

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

from math import *

import inkex
import simplestyle
import sys

def draw_SVG_circle(radius, (cx, cy), parent, start_end=(0, 2*pi), transform='' ):
    style = {   'stroke'        : '#000000',
                'stroke-width'  : '0.1',
                'fill'          : 'none' }

    circle_attribs = { 'style':simplestyle.formatStyle(style),
                       inkex.addNS('cx','sodipodi')    :str(cx),
                       inkex.addNS('cy','sodipodi')    :str(cy),
                       inkex.addNS('rx','sodipodi')    :str(radius),
                       inkex.addNS('ry','sodipodi')    :str(radius),
                       inkex.addNS('start','sodipodi') :str(start_end[0]),
                       inkex.addNS('end','sodipodi')   :str(start_end[1]),
                       inkex.addNS('open','inkscape')  :'true',    #all ellipse sectors we will draw are open
                       inkex.addNS('type','sodipodi')  :'arc',
                       'transform'                     :transform }

    inkex.etree.SubElement(parent, inkex.addNS('path','svg'), circle_attribs )

def draw_SVG_line(x1, y1, x2, y2, width, name, parent, color='#000000'):
    style = { 'stroke'      : color,
              'stroke-width': str(width),
              'marker-start': 'url(#Arrow2Mstart)',
              'fill'        : 'none' }

    line_attribs = { 'style':simplestyle.formatStyle(style),
                     inkex.addNS('label','inkscape'):name,
                     'd':'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2)}

    inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )

def draw_scaffold_lines_in_circle_v((cx, cy), radius, spacing, name, root=None, offset=0, color='#000000', transform='', new_layer=False, index=0):
    subdivisions = int(ceil(radius / spacing)) #integer subdivisions

    parent = root

    if new_layer:
        layer = inkex.etree.SubElement(root, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), name)
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        parent = layer

    if index % 2 == 0:
        if offset > 0:
            flip = True
        else:
            flip = False

        for i in range(-subdivisions, subdivisions+1):
            dx = i*spacing

            if abs(dx) < radius:
                dy = sqrt(abs(radius**2 - (dx-offset)**2))
                x1 = cx + dx - offset
                x2 = cx - dx + offset
                y1 = cy - dy
                y2 = cy + dy

                if flip:
                    draw_SVG_line(x1, y1, x1, y2, 0.5, str(i), parent, color=color),
                else:
                    draw_SVG_line(x1, y2, x1, y1, 0.5, str(i), parent, color=color),

                flip = not flip
    else:
        if offset > 0:
            flip = True
        else:
            flip = False

        for i in range(-subdivisions, subdivisions+1):
            dy = i*spacing

            if abs(dy) < radius:
                dx = sqrt(abs(radius**2 - (dy-offset)**2))
                y1 = cy + dy - offset
                y2 = cy - dy + offset
                x1 = cx - dx
                x2 = cx + dx

                if flip:
                    draw_SVG_line(x1, y1, x2, y1, 0.5, str(i), parent, color=color),
                else:
                    draw_SVG_line(x2, y1, x1, y1, 0.5, str(i), parent, color=color),

                flip = not flip

    return parent

class GenerateScaffold(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--radius",
                                     action="store", type="int",
				     dest="radius", default=12,
				     help="radius")
        self.OptionParser.add_option("--cx",
                                     action="store", type="int",
				     dest="cx", default=100,
				     help="cx")
        self.OptionParser.add_option("--cy",
                                     action="store", type="int",
				     dest="cy", default=70,
				     help="cy")
        self.OptionParser.add_option("--type",
                                     action="store", type="string",
		                     dest="type", default='circle',
				     help="Scaffold Type")
        self.OptionParser.add_option("--spacing",
                                     action="store", type="float",
                                     dest="spacing", default=0.4,
                                     help="spacing")
        self.OptionParser.add_option("--layers",
                                     action="store", type="int",
                                     dest="layers", default=1,
                                     help="layers")


    def effect(self):
        svgDocumentRoot = self.document.getroot()
        baseLayer = inkex.etree.SubElement(svgDocumentRoot, 'g')
        baseLayer.set(inkex.addNS('label', 'inkscape'), 'baseLayer')
        baseLayer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        parent = baseLayer

        draw_SVG_circle(inkex.uuconv['mm'] * self.options.radius,
                        (inkex.uuconv['mm'] * self.options.cx,
                         inkex.uuconv['mm'] * self.options.cy),
                        parent)


        for l in range(0, self.options.layers):
            layer = draw_scaffold_lines_in_circle_v((inkex.uuconv['mm'] * self.options.cx,
                                                     inkex.uuconv['mm'] * self.options.cy),
                                                    inkex.uuconv['mm'] * self.options.radius,
                                                    inkex.uuconv['mm'] * self.options.spacing,
                                                    'Scaffold Layer %.2d' % (l), root = svgDocumentRoot,
                                                    color='#0000ff', new_layer = True, index=l)

            draw_scaffold_lines_in_circle_v((inkex.uuconv['mm'] * self.options.cx,
                                             inkex.uuconv['mm'] * self.options.cy),
                                            inkex.uuconv['mm'] * self.options.radius,
                                            inkex.uuconv['mm'] * self.options.spacing,
                                            'Scaffold Layer %.2d' % (l), root=layer, color='#ff0000',
                                            offset = (self.options.spacing / 2)*inkex.uuconv['mm'],
                                            new_layer = False, index=l)

if __name__ == '__main__':
    e = GenerateScaffold()
    e.affect()
