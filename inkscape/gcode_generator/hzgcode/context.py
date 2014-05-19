from math import *
import sys

class GCodeContext:
    def __init__(self, travel_feedrate, xy_feedrate, z_height, thread_width, temp, home, startGcode, filament, ex2color, ex2offsetX, ex2offsetY, ex2offsetZ, ex2feedrate, ex2Ainc, file):
      self.travel_feedrate = travel_feedrate
      self.xy_feedrate = xy_feedrate
      self.zHeight = z_height
      self.threadWidth = thread_width
      self.temp = temp
      self.home = home
      self.startGcode = startGcode
      self.filament = filament
      self.ex2color = ex2color
      self.ex2offsetX = ex2offsetX
      self.ex2offsetY = ex2offsetY
      self.ex2offsetZ = ex2offsetZ
      self.ex2feedrate = ex2feedrate
      self.ex2Ainc = ex2Ainc
      self.file = file
      self.drawing = False
      self.retracted = False
      self.last = 0,0
      self.e = 0.0
      self.z = 0.0;
      self.a = 0.0
      self.currentColor = "default"
      self.currentExtruder = 0
      self.switchedExtruder = False

      self.preamble = []
      if startGcode != "" :
        self.preamble.append(startGcode + "\n")

      if home == "true" :
        self.preamble.append("G28 X0 Y0 Z0 ; move to the endstops and call that position 0,0,0 \n")
      self.preamble.append("G0 Z0\n")

      self.postscript = [
        "(====== Finished last layer ======)",
        "(====== Move away from part =====)",
        "M5",
        "M9",
        "G0 X0 Y0 F%.2f" % (self.travel_feedrate * 60),
      ]

      self.registration = [
         ""
      ]

      self.sheet_header = [
        "(start of sheet header)",
        ""
      ]

      self.sheet_footer = [
        ""
        ]

      self.loop_forever = [ "M30 (Plot again?)" ]

      self.codes = []

    def start(self):
      if (self.retracted):
        self.e += 5
        #self.codes.append("G1 E%0.4f (de-retract some)" %(self.e))
        self.retracted = False
      if self.switchedExtruder:
        if self.currentExtruder == 0:
          self.codes.append("M3 S1000")
        elif self.currentExtruder == 1:
          self.a -= 0.2
          self.codes.append("G1 A%.2F F100" % (self.a))
          #self.codes.append("G4 P1")
          self.codes.append("F%.2f" % (self.ex2feedrate * 60))
        self.switchedExtruder = False
      self.drawing = True

    def stop(self):
      if (self.retracted == False):
        self.e += -5
        #self.codes.append("G1 E%0.4f (retract some)" %(self.e))
        self.retracted = True
      self.drawing = False

    def go_to_point(self, x, y, stop=False):
      if self.last == (x,y):
        return
      if stop:
        return
      else:
        if self.drawing:
          self.stop(self)
        if self.currentExtruder == 0:
            self.codes.append("G0 X%.2f Y%.2f F%.2f" % (x,y, self.travel_feedrate * 60))
        elif self.currentExtruder == 1:
            self.codes.append("G0 Z%.2f" % (self.z + 0.4)) # hop over
            self.codes.append("G0 X%.2f Y%.2f F%.2f" % (x + self.ex2offsetX,y + self.ex2offsetY, self.travel_feedrate * 60))
            self.codes.append("G0 Z%.2f" % (self.z))
      self.last = (x,y)

    def draw_to_point(self, x, y, width, layerHeight, stop=False):
      if self.last == (x,y):
          return
      if stop:
        return
      else:
        if self.drawing == False:
          self.start(self)
        lx = x - self.last[0]
        ly = y - self.last[1]
        self.e += self.calculateE( lx , ly , self.zHeight, self.threadWidth, self.filament/2)
        if self.currentExtruder == 0:
            #TODO: calculate feedrate for line width
            self.codes.append("G1 X%0.2f Y%0.2f F%0.2f" % (x,y, self.xy_feedrate * 60))
        elif self.currentExtruder == 1:
            self.a -= self.calculateA( lx , ly , self.zHeight, self.threadWidth, self.filament/2)
            self.codes.append("G1 X%0.2f Y%0.2f A%0.2f" % (x + self.ex2offsetX, y + self.ex2offsetY, self.a))
      self.last = (x,y)

    def calculateA(self, x, y, z, thread, radius=1.45):
      l = hypot(x,y)
      return (l * z * thread ) / (pi * radius**2 )
      #return self.ex2Ainc

    def calculateE(self, x, y, z, thread, radius=1.45):
      "calculate the relative E component based on x y z vector and thread width"
      l = hypot(x,y)
      return (l * z * thread ) / (pi * radius**2 )

    def switchExtruder(self, color=''):
      "determine if we need to switch extruders and append the needed gcode if so"
      if self.currentColor == color:
        #self.codes.append( ";(same color, no switch:" + color + ")")
        return
      self.codes.append( ";(old color:" + self.currentColor + " new color:" + color + ")")
      if color == self.ex2color:
        #switch to new extruder
        self.codes.append("M5")
        #self.codes.append("G92 X%0.2f Y%0.2f Z%0.2f" % (self.last[0] + self.ex2offsetX,
        #                                                self.last[1] + self.ex2offsetY,
        #                                                self.z - self.ex2offsetZ))
        self.codes.append("T1")
        self.codes.append("G0 Z%0.2f" % (self.z + self.ex2offsetZ))
        self.currentExtruder = 1
        self.switchedExtruder = True

      if self.currentColor == self.ex2color:
        #and switch back again
        self.a += 0.2
        self.codes.append("G0 A%.2f F100" % (self.a))
        #self.codes.append("G92 X%0.2f Y%0.2f Z%0.2f" % (self.last[0] - self.ex2offsetX,
        #                                                self.last[1] - self.ex2offsetY,
        #                                                self.z + self.ex2offsetZ))
        self.codes.append("T0")
        self.codes.append("G0 Z%0.2f" % (self.z))
        self.currentExtruder = 0
        self.switchedExtruder = True
      #note this only reacts to the 2nd extruder color, all else is treated as it were the default extruder
      if self.currentColor == "default":
        self.currentExtruder = 0
        self.switchedExtruder = True
      self.currentColor = color
      return



    def generate(self):

      codesets = [self.codes]

      for line in self.preamble:
        print line

      for codeset in codesets:
        for line in codeset:
            print line
        if codeset :
          print "G0 Z%.2f" % (self.z + 5.5)
          for line in self.postscript:
              print line
