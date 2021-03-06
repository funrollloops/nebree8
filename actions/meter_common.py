import logging
from time import time, sleep
from actions.action import ActionException
from parts import load_cell

#OZ_TO_ADC_VALUES = 30  # True calibration
#OZ_TO_ADC_VALUES = 39.  # +30% for generous pours.
OZ_TO_ADC_VALUES = 1.4 # For the nano load cell. SHould be 1.0, but something is funny
MAX_TARE_STDDEV = 4.
TARE_TIMEOUT_SECS = 20.
SECONDS_PER_OZ = 10 * .75 * 1.25


class TareTimeout(ActionException):
  """Thrown when attempt to tare times out"""


def tare(robot):
  """Waits for load cell readings to stabilize.

  returns: load_cell.Summary
  throws: Exception
  """
  tare_start = time()
  tare = robot.load_cell.recent_summary(n=2)
  while (tare.stddev > MAX_TARE_STDDEV and
         time() < tare_start + TARE_TIMEOUT_SECS):
    sleep(.1)
    tare = robot.load_cell.recent_summary(n=2)
  if tare.stddev > MAX_TARE_STDDEV:
    logging.error('Reading standard deviation while taring above ' +
                  '%s for %s secs. Last result: %s' % (MAX_TARE_STDDEV,
                                                       TARE_TIMEOUT_SECS, tare))
    tare = load_cell.Summary(*(tare[:4] + (False,)))
  return tare
