print(__file__)

"""
ProcedureRegistry for USAXS

EXAMPLE::

    use_mode = ProcedureRegistry(name="use_mode")

    def clearScalerNames():
        for ch in scaler.channels.configuration_attrs:
            if ch.find(".") < 0:
                chan = scaler.channels.__getattribute__(ch)
                chan.chname.put("")

    def setMyScalerNames():
        scaler.channels.chan01.chname.put("clock")
        scaler.channels.chan02.chname.put("I0")
        scaler.channels.chan03.chname.put("detector")

    def useMyScalerNames(): # Bluesky plan
        yield from bps.mv(
            m1, 5,
            use_mode, "clearScalerNames",
        )
        yield from bps.mv(
            m1, 0,
            use_mode, "setMyScalerNames",
        )

    def demo():
        print(1)
        m1.move(5)
        print(2)
        time.sleep(2)
        print(3)
        m1.move(0)
        print(4)


    use_mode.add(demo)
    use_mode.add(clearScalerNames)
    use_mode.add(setMyScalerNames)
    # use_mode.set("demo")
    # use_mode.set("clearScalerNames")
    # RE(useMyScalerNames())

"""


class ProcedureRegistry(Device):
    """
    Procedure Registry
    
    With many instruments, such as USAXS,, there are several operating 
    modes to be used, each with its own setup code.  This ophyd Device
    should coordinate those modes so that the setup procedures can be called
    either as part of a Bluesky plan or from the command line directly.

    Assumes that users will write functions to setup a particular 
    operation or operating mode.  The user-written functions may not
    be appropriate to use in a plan directly since they might
    make blocking calls.  The ProcedureRegistry will call the function
    in a thread (which is allowed to make blocking calls) and wait
    for the thread to complete.
    
    It is assumed that each user-written function will not return until
    it is complete.

    .. autosummary::
       
        ~dir
        ~add
        ~remove
        ~set
        ~put

    """
    
    busy = Signal(value=False, name="busy")
    registry = {}
    delay_s = 0
    timeout_s = None
    state = "__created__"
    
    @property
    def dir(self):
        """tuple of procedure names"""
        return tuple(sorted(self.registry.keys()))
    
    def add(self, procedure):
        """
        add procedure to registry

        procedure (function) : function
        """
        #if procedure.__class__ == "function":
        self.registry[procedure.__name__] = procedure
    
    def remove(self, procedure):
        """
        remove procedure from registry

        procedure (function) : function
        """
        #if procedure.__class__ == "function":
        if procedure.__name__ in self.registry:
            del self.registry[procedure.__name__]
    
    def set(self, proc_name):
        """
        run procedure in a thread, return once it is complete
        
        proc_name (str) : name of registered procedure to be run
        """
        if not isinstance(proc_name, str):
            raise ValueError("expected a procedure name, not {}".format(proc_name))
        if proc_name not in self.registry:
            raise KeyError("unknown procedure name: "+proc_name)
        if self.busy.value:
            raise RuntimeError("busy now")
 
        self.state = "__busy__"
        status = DeviceStatus(self)
        
        @APS_plans.run_in_thread
        def run_and_delay():
            self.busy.put(True)
            self.registry[proc_name]()
            # optional delay
            if self.delay_s > 0:
                time.sleep(self.delay_s)
            self.busy.put(False)
            status._finished(success=True)
        
        run_and_delay()
        ophyd.status.wait(status, timeout=self.timeout_s)
        self.state = proc_name
        return status
    
    def put(self, value):   # TODO: risky?
        """replaces ophyd Device default put() behavior"""
        self.set(value)


use_mode = ProcedureRegistry(name="ProcedureRegistry")
