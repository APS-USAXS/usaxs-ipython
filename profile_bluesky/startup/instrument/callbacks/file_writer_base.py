
"""
define a base for file writer callbacks
"""

__all__ = ["FileWriterCallbackBase",]

from ..session_logs import logger
logger.info(__file__)

# TODO: contribute FileWriterCallbackBase to apstools.filewriters

class FileWriterCallbackBase:
    """
    applications should subclass and rewrite the ``writer()`` method
    """

    def __init__(self, *args, **kwargs):
        self.clear()
        self.xref = dict(
            bulk_events = self.bulk_events,
            datum = self.datum,
            descriptor = self.descriptor,
            event = self.event,
            resource = self.resource,
            start = self.start,
            stop = self.stop,
            )

    def receiver(self, key, doc):
        """
        bluesky callback (handles a stream of documents)
        """
        handler = self.xref.get(key)
        if handler is None:
            logger.error("unexpected key %s" % key)
        else:
            handler(doc)

        # - - - - - - - - - - - - - - -
 
    def clear(self):
        self.acquisitions = {}
        self.exit_status = None
        self.metadata = {}
        self.scanning = False
        self.scan_id = None
        self.streams = {}
        self.start_time = None
        self.stop_reason = None
        self.stop_time = None
        self.uid = None
   
    def writer(self):
        """
        print summary of run as diagnostic

        override this method in subclass to write a file
        """
        print("write to file now.")

        keys = "scan_id exit_status start_time stop_reason stop_time uid".split()
        for k in sorted(keys):
            print(f"{k} = {getattr(self, k)}")

        for k, v in sorted(self.metadata.items()):
            print(f"metadata {k}: {v}")

        for k, v in sorted(self.streams.items()):
            if len(v) != 1:
                print("expecting only one descriptor in stream %s, found %s" % (k, len(v)))
            else:
                data = self.acquisitions[v[0]]["data"]
                num_vars = len(data)
                symbol = list(data.keys())[0]   # get the key (symbol) of first data object
                if num_vars == 0:
                    num_values = 0
                else:
                    num_values = len(data[symbol]["data"])
                # msg = f"stream:{k} uids={v} num_vars={num_vars} num_values={num_values}"
                msg = f"stream:{k} num_vars={num_vars} num_values={num_values}"
                print(msg)

        print(f"elapsed scan time: {self.stop_time-self.start_time:.3f}s")

    # - - - - - - - - - - - - - - -
    
    def bulk_events(self, doc):
        if not self.scanning:
            return

    def datum(self, doc):
        if not self.scanning:
            return

    def descriptor(self, doc):
        if not self.scanning:
            return
        stream = doc["name"]
        uid = doc["uid"]

        if stream not in self.streams:
            self.streams[stream] = []
        self.streams[stream].append(uid)

        if uid not in self.acquisitions:
            self.acquisitions[uid] = dict(
                stream = stream,
                data = {}
            )
        data = self.acquisitions[uid]["data"]
        for k, entry in doc["data_keys"].items():
            dd = data[k] = {}
            dd["source"] = entry.get("source", 'local')
            dd["dtype"] = entry.get("dtype", '')
            dd["shape"] = entry.get( "shape", [])
            dd["units"] = entry.get("units", '')
            dd["lower_ctrl_limit"] = entry.get("lower_ctrl_limit", '')
            dd["upper_ctrl_limit"] = entry.get("upper_ctrl_limit", '')
            dd["precision"] = entry.get("precision", 0)
            dd["object_name"] = entry.get("object_name", k)
            dd["data"] = []    # entry data goes here
            dd["time"] = []    # entry time stamps here

    def event(self, doc):
        if not self.scanning:
            return
        uid = doc["uid"]
        descriptor_uid = doc["descriptor"]
        seq_num = doc["seq_num"]
        
        # gather the data by streams
        descriptor = self.acquisitions.get(descriptor_uid)
        if descriptor is not None:
            for k, v in doc["data"].items():
                data = descriptor["data"].get(k)
                if data is None:
                    print("entry key %s not found in descriptor of %s" % (k, descriptor["stream"]))
                else:
                    data["data"].append(v)
                    data["time"].append(doc["timestamps"][k])

    def resource(self, doc):
        if not self.scanning:
            return

    def start(self, doc):
        self.clear()
        self.scanning = True
        self.scan_id = doc["scan_id"] or 0
        self.start_time = doc["time"]
        self.uid = doc["uid"]

        # gather the metadata
        for k, v in doc.items():
            if k in "scan_id time uid".split():
                continue
            self.metadata[k] = v

    def stop(self, doc):
        if not self.scanning:
            return
        self.status = doc["exit_status"]
        self.stop_reason  = doc["reason"]
        self.stop_time = doc["time"]

        self.writer()
