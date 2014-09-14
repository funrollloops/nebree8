#!/usr/bin/env python

import webapp2
import BaseHTTPServer
import logging
import re
import socket
import time

from actions.compressor import CompressorToggle
from actions.compressor import State
from actions.home import Home
from actions.meter import Meter
from actions.move import Move
from actions.vent import Vent
from controller import Controller
import ingredients

robot = None
controller = None

WT_TO_OZ = 1.0


def GetTemplate(filename):
    return open('templates/' + filename).read()


def ServeFile(filename):
    class ServeFileImpl(webapp2.RequestHandler):
        def get(self):
            self.response.write(GetTemplate(filename))
    return ServeFileImpl


class LoadCellJson(webapp2.RequestHandler):
    def get(self):
        self.response.write("[")
        self.response.write(','.join('[%s, %f]' % rec
                            for rec in robot.load_cell.recent(1000)))
        self.response.write("]")


class MakeTestDrink(webapp2.RequestHandler):
    def get(self):  # TODO: Switch to post.
        controller.EnqueueGroup([
            Home(),
            Move(5),
            Meter(valve_to_actuate=1, oz_to_meter=1),
            Move(10),
            Meter(valve_to_actuate=2, oz_to_meter=2),
        ])
        self.response.write("Queued.")


class InspectQueue(webapp2.RequestHandler):
    def get(self):
        """Displays the state of the action queue."""
        actions = controller.InspectQueue()
        content = []
        if not actions:
            content.append("Queue is empty")
        else:
            for action in actions:
                name, props = action.inspect()
                content.append(name)
                for prop in props.items():
                  content.append('\t%s: %s' % prop)
        self.response.write(GetTemplate('queue.html').format(
          exception=controller.last_exception, content='\n'.join(content),
          robot_dict=robot.__dict__))

META_REFRESH="""
<html>
  <head>
    <title>{msg}</title>
    <meta http-equiv="refresh" content="2;URL={url}">
  </head>
<body>
{msg}
</body>
</html>
"""

class RetryQueue(webapp2.RequestHandler):
  def post(self):
    if controller.last_exception:
      controller.Retry()
    self.response.write(META_REFRESH.format(msg="Retrying...", url="/queue"))


class ClearQueue(webapp2.RequestHandler):
  def post(self):
    if controller.last_exception:
      controller.ClearAndResume()
    self.response.write(META_REFRESH.format(msg="Cleared...", url="/queue"))


class SkipQueue(webapp2.RequestHandler):
  def post(self):
    if controller.last_exception:
      controller.SkipAndResume()
    self.response.write(META_REFRESH.format(msg="Skipped...", url="/queue"))


class StaticFileHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(open(self.ToRelativePath(self.request.path)).read())
    def ToRelativePath(self, path):
        if (len(path) > 0 and path[0] == "/"):
            return path[1:]


class RobotControlHandler(webapp2.RequestHandler):
    def post(self):
        command = self.request.get("command")
        details = self.request.get("text")
        print command
        print details
        if "calibrate" in command:
          controller.EnqueueGroup([
              Home(),
          ])
        elif "drink" in command:
          target_composition = None
          print "DRINK COMMAND: %s" % command
          if "test" in command:
            print "DRINK COMMAND: %s" % command
            ingredient_to_wt_loc = ingredients.CreateTestDrink()
          elif "sour drink" in command:
            target_composition = [2, 1, 1, 0]
            ingredient_to_wt_loc = ingredients.CreateRandomDrink(target_composition)
          else:
            target_composition = [4, 1, 0, 1]
            ingredient_to_wt_loc = ingredients.CreateRandomDrink(target_composition)
          actions = []
          for ingredient, (wt, loc) in ingredient_to_wt_loc.iteritems():
            print "%s oz of %s at %f on valve %s" % (wt, ingredient, loc, loc)
            actions.append(Move(-10.5 - 4.0 * (14 - loc)))
            actions.append(Meter(valve_to_actuate=loc, oz_to_meter=(wt * WT_TO_OZ)))
          actions.append(Home())
          controller.EnqueueGroup(actions)
        elif "fill" in command:
          oz, valve = details.split(",")
          oz = float(oz)
          valve = int(valve)
          controller.EnqueueGroup([
              Meter(valve_to_actuate = valve, oz_to_meter = oz),
          ])
        elif "move" in command:
          controller.EnqueueGroup([
              Move(float(details)),
          ])
        elif "vent" in command:
          controller.EnqueueGroup([
              Vent(),
          ])
        elif "compressor on" in command:
          controller.EnqueueGroup([
              CompressorToggle(State.ON)
          ])
        elif "compressor off" in command:
          controller.EnqueueGroup([
              CompressorToggle(State.OFF)
          ])
        self.response.write("ok")
    def get(self):
        print "Shouldn't call get!"


class PausableWSGIApplication(webapp2.WSGIApplication):
  def __init__(self, routes=None, debug=False, config=None):
    super(PausableWSGIApplication, self).__init__(routes=routes, debug=debug, config=config)
    self.drop_all = False

  def __call__(self, environ, start_response):
    while self.drop_all:
      time.sleep(1.0)
    return super(PausableWSGIApplication, self).__call__(environ, start_response)

def StartServer(port):
    from paste import httpserver

    logging.basicConfig(
        filename="/dev/stdout",
        #filename="server_%s.log" % time.strftime("%Y%m%d_%H%M%S"),
        filemode='w',
        level=logging.INFO)
    #app = webapp2.WSGIApplication([
    app = PausableWSGIApplication([
        ('/', ServeFile('index.html')),
        ('/test_drink', MakeTestDrink),
        ('/load_cell', ServeFile('load_cell.html')),
        ('/load_cell.json', LoadCellJson),
        ('/queue', InspectQueue),
        ('/queue-retry', RetryQueue),
        ('/queue-clear', ClearQueue),
        ('/queue-skip', SkipQueue),
        ('/robot-control', RobotControlHandler),
        ('/templates/.*', StaticFileHandler),
        ('/bower_components/.*', StaticFileHandler)
    ])
    controller.app = app
    print "serving at http://%s:%i" % (socket.gethostname(), port)
    # from multiprocessing import Pool
    # pool = Pool(5)
    # while True:
    #   while app.drop_all:
    #     time.sleep(1.0)
    httpserver.serve(app, host="0.0.0.0", port=port, start_loop=True)  #, use_threadpool=pool)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="N.E.BRE-8 control server")
    parser.add_argument('--port', type=int, default=8000, help='Port to run on')
    parser.add_argument('--fake', dest='fake', action='store_true')
    parser.add_argument('--nofake', dest='fake', action='store_false')
    parser.set_defaults(fake=False)
    args = parser.parse_args()

    global robot
    global controller
    if args.fake:
        from fake_robot import FakeRobot
        robot = FakeRobot()
    else:
        from physical_robot import PhysicalRobot
        robot = PhysicalRobot()
    controller = Controller(robot)
    StartServer(args.port)

if __name__ == "__main__":
    main()