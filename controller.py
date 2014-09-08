#!/usr/bin/env python

import threading
import collections

class Controller:
  def __init__(self, robot):
    self.current_action = None
    self.queue = collections.deque()
    self.queued_sem = threading.Semaphore(0)
    self.queue_lock = threading.Lock()
    self.robot = robot
    self.thread = threading.Thread(target=self._Process)
    self.thread.daemon = True
    self.thread.start()

  def _Process(self):
    while True:
      self.queued_sem.acquire() # Ensure there are items to process.
      with self.queue_lock:
        self.current_action = self.queue.popleft()
      self.current_action(self.robot)

  def EnqueueGroup(self, action_group):
    with self.queue_lock:
      for action in action_group:
        self.queue.append(action)
        # Signal that there are items to process.
        self.queued_sem.release() 

  def InspectQueue(self):
    with self.queue_lock:
      return (([self.current_action] if self.current_action else []) +
          list(self.queue))
