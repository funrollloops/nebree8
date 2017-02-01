#!/usr/bin/python

import RPi.GPIO as gpio
import io_bank
import subprocess
import sys
import time

# dir_pin = 7
# pul_pin = 8
# en_pin = 25

#3.75 inches per revolution

# output_pins = (
#     dir_pin,
#     pul_pin,
#     en_pin)

# def Setup():
#   gpio.setmode(gpio.BCM)
#   gpio.setwarnings(False)
#   for pin in output_pins:
#     gpio.setup(pin, gpio.OUT)
# gpio.output(en_pin, 0)


def trusty_sleep(n):
  return time.sleep(n)
  # start = time.time()
  # while (time.time() - start < n):
  #   #time.sleep(n - (time.time() - start))
  #   pass


class StepperMotor(object):
  def __init__(self, dry_run=False, io=None, use_separate_process=False):
    self.pulse_state = False
    self.use_separate_process = use_separate_process
    self.use_arduino = True
    self.dry_run = dry_run
    if not io:
      io = io_bank.IOBank()
    self.io = io
    if not self.use_arduino:
      self.colliding_positive = not self.io.ReadInput(
          io_bank.Inputs.LIMIT_SWITCH_POS)
      self.colliding_negative = not self.io.ReadInput(
          io_bank.Inputs.LIMIT_SWITCH_NEG)

      def HitPositiveRail(channel):
        time.sleep(0.0001)
        self.colliding_positive = not self.io.ReadInput(
            io_bank.Inputs.LIMIT_SWITCH_POS)
        print "Hit positive rail"

      def HitNegativeRail(channel):
        #self.colliding_negative = True
        time.sleep(0.0001)
        self.colliding_negative = not self.io.ReadInput(
            io_bank.Inputs.LIMIT_SWITCH_NEG)
        print "Hit negative rail"

      self.io.AddCallback(io_bank.Inputs.LIMIT_SWITCH_POS, gpio.FALLING,
                          HitPositiveRail)
      self.io.AddCallback(io_bank.Inputs.LIMIT_SWITCH_NEG, gpio.FALLING,
                          HitNegativeRail)

  def Move(self,
           steps,
           forward=1,
           ramp_seconds=0,
           final_wait=0.0005,
           max_wait=4000,
           ice_steps=None):
    if ice_steps is None:
      ice_steps = steps
    if self.dry_run:
      print "DRY RUN: Moving %d steps in direction: %d" % (steps, forward)
    else:
      print "Moving %d steps in direction: %d" % (steps, forward)
    if self.use_arduino:
      return self.io.Move(forward, steps, ice_steps, final_wait)

    if self.use_separate_process:
      if forward:
        backward = "False"
      else:
        backward = "True"
      subprocess.call(
          "sudo nice -n -19 sudo ./motor.py --steps %d --backward=%s" %
          (steps, backward),
          shell=True)
      return
    self.io.WriteOutput(io_bank.Outputs.STEPPER_PULSE, 0)
    self.io.WriteOutput(io_bank.Outputs.STEPPER_DIR, forward)
    #gpio.output(pul_pin, 0)
    #gpio.output(dir_pin, forward)
    initial_wait = 0.002
    current_wait = initial_wait
    # current_wait = 0.001
    # final_wait = 0.001
    for i in range(steps):
      if (not ((self.colliding_positive and forward) or
               (self.colliding_negative and not forward))):
        #print self.pulse_state
        self.io.WriteOutput(io_bank.Outputs.STEPPER_PULSE,
                            int(self.pulse_state))
        #gpio.output(pul_pin, int(self.pulse_state))
        #time.sleep(0.001)  # one millisecond
        #trusty_sleep(0.001)
        #trusty_sleep(0.0002)
        trusty_sleep(current_wait)
        self.pulse_state = not self.pulse_state
      if forward:
        self.colliding_negative = False
      else:
        self.colliding_positive = False
      if steps - i > 600:
        if current_wait > final_wait:
          current_wait *= 0.996
          pass
      else:
        if current_wait < initial_wait:
          current_wait *= 1.004
          pass
    self.io.WriteOutput(io_bank.Outputs.STEPPER_PULSE, 0)


def InchesToSteps(inches):
  return int(inches / 2.81 * 800)  # 14 teeth -> 2.81 inches


def StepsToInches(steps):
  return steps * 2.81 / 800


class RobotRail(object):
  def __init__(self, motor):
    self.motor = motor
    self.position = 0

  def FillPositions(self, absolute_positions, ice_percent=0.0):
    for position in absolute_positions:
      forward = position > self.position
      steps = InchesToSteps(abs(position - self.position))
      ice_steps = steps * (1.0 - ice_percent)
      self.motor.Move(steps, forward=forward)
      if forward:
        self.position += StepsToInches(steps + 2)
      else:
        self.position -= StepsToInches(steps + 2)
      print "At position: %f" % position

  def CalibrateToZero(self, carefully=True):
    print "CalibrateToZero"
    steps = InchesToSteps(70)
    # if not carefully:
    #   self.FillPositions([0])
    #   self.motor.Move(InchesToSteps(200), forward=True, final_wait=0.002)
    # else:
    self.motor.Move(steps, forward=True)  #, final_wait=0.01)
    self.position = 0
