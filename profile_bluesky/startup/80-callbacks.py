print(__file__)

# custom callbacks

import APS_BlueSky_tools.callbacks
import APS_BlueSky_tools.filewriters

# collect last scan's documents into doc_collector.documents
doc_collector = APS_BlueSky_tools.callbacks.DocumentCollectorCallback()
callback_db['doc_collector'] = RE.subscribe(doc_collector.receiver)


# temporary until library is fixed
import datetime
class mySpecWriterCallback(APS_BlueSky_tools.filewriters.SpecWriterCallback):

    def receiver(self, key, document):
        """BlueSky callback: receive all documents for handling"""
        xref = dict(
            start = self.start,
            descriptor = self.descriptor,
            event = self.event,
            bulk_events = self.bulk_events,
            stop = self.stop,
        )
        logger = logging.getLogger(__name__)
        if key in xref:
            logger.debug("{} document, uid={}".format(key, document["uid"]))
            self._datetime = datetime.datetime.fromtimestamp(document["time"])
            xref[key](document)
        else:
            msg = "custom_callback encountered: {} : {}".format(key, document)
            # raise ValueError(msg)
            logger.warning(msg)
        return


# write scans to SPEC data file
specwriter = mySpecWriterCallback()
# make the SPEC file in /tmp (assumes OS is Linux)
specwriter.newfile(os.path.join("/tmp", specwriter.spec_filename))
callback_db['specwriter'] = RE.subscribe(specwriter.receiver)
print("writing to SPEC file: " + specwriter.spec_filename)
