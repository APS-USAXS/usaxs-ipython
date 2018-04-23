print(__file__)

"""
APS Fly Scan example using the busy record

Alternative approach to the BlueSky Flyer,
this example does not inject the data into BlueSky.
Coded here to meet an imposing deadline.
"""

logger = logging.getLogger(os.path.split(__file__)[-1])


from collections import deque, OrderedDict
import os
import subprocess
from ophyd.utils import OrderedDefaultDict
from enum import Enum
import threading
import time


class BusyStatus(str, Enum):
    busy = "Busy"
    done = "Done"


class BusyRecord(Device):
    """a busy record sets the fly scan into action"""
    state = Component(EpicsSignal, "")
    output_link = Component(EpicsSignal, ".OUT")
    forward_link = Component(EpicsSignal, ".FLNK")


class MyCalc(Device):
    """swait record simulates a signal"""
    result = Component(EpicsSignal, "")
    calc = Component(EpicsSignal, ".CALC")
    proc = Component(EpicsSignal, ".PROC")


class MyWaveform(Device):
    """waveform records store fly scan data"""
    wave = Component(EpicsSignalRO, "")
    number_elements = Component(EpicsSignalRO, ".NELM")
    number_read = Component(EpicsSignalRO, ".NORD")


# FIXME: this Device does not work correctly.  DO NOT USE.
#	class ApsBusyFlyScanDeviceMixin(object):
#		"""
#		support APS Fly Scans that are operated by a busy record
#		
#		requires that calling class create an instance of ``BusyRecord``
#		named ``busy``, as in::
#
#			busy = Component(BusyRecord, 'prj:mybusy')
#
#		This mixin will not generate BlueSky events to inject data into
#		the databroker.  Any data collection must be handled during
#		the various hook functions.
#		
#		.. autosummary:
#		   ~flyscan_plan
#		   ~hook_flyscan_plan
#		   ~hook_pre_flyscan_plan
#		   ~hook_flyscan_wait_not_scanning
#		   ~hook_flyscan_wait_scanning
#		   ~hook_post_flyscan_plan
#		   ~flyscan_wait
#		   ~_flyscan
#		
#		EXAMPLE::
#
#			class ApsBusyFlyScanDevice(Device, ApsBusyFlyScanDeviceMixin):
#				'''
#				BlueSky interface for the busyExample.py fly scan
#				'''
#				busy = Component(BusyRecord, 'prj:mybusy')
#				# motor = Component(EpicsMotor, 'prj:m1')
#				signal = Component(MyCalc, 'prj:userCalc1')
#				xArr = Component(MyWaveform, 'prj:x_array')
#				yArr = Component(MyWaveform, 'prj:y_array')
#				
#				def __init__(self, **kwargs):
#					super().__init__('', parent=None, **kwargs)
#					self.update_interval = 10
#					self.update_time = time.time() + self.update_interval
#				
#				... plus various overrides
#
#		"""
#
#		def __init__(self, **kwargs):
#			self._flyscan_status = None
#			self.poll_sleep_interval_s = 0.05
#		
#		def hook_flyscan_plan(self):
#			"""
#			Customize: called during fly scan
#			
#			called from RunEngine thread in ``flyscan_plan()``, 
#			blocking calls are not permitted
#			"""
#			logger.debug("hook_flyscan_plan() : no-op default")
#		
#		def hook_pre_flyscan_plan(self):
#			"""
#			Customize: called before the fly scan
#			
#			NOTE: As part of a BlueSky plan thread, no blocking calls are permitted
#			"""
#			logger.debug("hook_pre_flyscan_plan() : no-op default")
#		
#		def hook_post_flyscan_plan(self):
#			"""
#			Customize: called after the fly scan
#			
#			NOTE: As part of a BlueSky plan thread, no blocking calls are permitted
#			"""
#			logger.debug("hook_post_flyscan_plan() : no-op default")
#		
#		def hook_flyscan_wait_not_scanning(self):
#			"""
#			Customize: called ``flyscan_wait(False)``
#			
#			called in separate thread, blocking calls are permitted
#			but keep it quick
#			"""
#			logger.debug("hook_flyscan_not_scanning() : no-op default")
#
#		def hook_flyscan_wait_scanning(self):
#			"""
#			Customize: called from ``flyscan_wait(True)``
#			
#			called in separate thread, blocking calls are permitted
#			but keep it quick
#			"""
#			logger.debug("hook_flyscan_wait_scanning() : no-op default")
#
#		def flyscan_wait(self, scanning):
#			"""
#			wait for the busy record to return to Done
#			
#			Call external hook functions to allow customizations
#			"""
#			msg = "flyscan_wait()"
#			msg += " scanning=" + str(scanning)
#			msg += " busy=" + str(self.busy.state.value)
#			logger.debug(msg)
#
#			if scanning:
#				hook = self.hook_flyscan_wait_scanning
#			else:
#				hook = self.hook_flyscan_wait_not_scanning
#
#			while self.busy.state.value not in (BusyStatus.done, 0):
#				hook()
#				time.sleep(self.poll_sleep_interval_s)  # wait to complete ...
#
#		def _flyscan(self):
#			"""
#			start the busy record and poll for completion
#			
#			It's OK to use blocking calls here 
#			since this is called in a separate thread
#			from the BlueSky RunEngine.
#			"""
#			logger.debug("_flyscan()")
#			if self._flyscan_status is None:
#				logger.debug("leaving fly_scan() - not complete")
#				return
#
#			logger.debug("_flyscan() - clearing Busy")
#			self.busy.state.put(BusyStatus.done) # make sure it's Done first
#			self.flyscan_wait(False)
#			time.sleep(1.0)
#
#			logger.debug("_flyscan() - setting Busy")
#			self.busy.state.put(BusyStatus.busy)
#			self.flyscan_wait(True)
#
#			self._flyscan_status._finished(success=True)
#			logger.debug("_flyscan() complete")
#		
#		def flyscan_plan(self, *args, **kwargs):
#			"""
#			This is the BlueSky plan to submit to the RunEgine
#			"""
#			logger.debug("flyscan_plan()")
#			yield from bps.open_run()
#
#			self.hook_pre_flyscan_plan()
#			self._flyscan_status = DeviceStatus(self.busy.state)
#			
#			thread = threading.Thread(target=self._flyscan, daemon=True)
#			thread.start()
#			
#			while not self._flyscan_status.done:
#				self.hook_flyscan_plan()
#				bps.sleep(self.poll_sleep_interval_s)
#			logger.debug("flyscan_plan() status=" + str(self._flyscan_status))
#
#			print("BEFORE<<<<<<<<<<<<<<<<<<<<<<<<<<")
#			self.hook_post_flyscan_plan()
#			print("AFTER<<<<<<<<<<<<<<<<<<<<<<<<<<")
#
#			yield from bps.close_run()
#			logger.debug("flyscan_plan() complete")
