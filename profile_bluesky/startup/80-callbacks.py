print(__file__)

# custom callbacks


# collect last scan's documents into doc_collector.documents
doc_collector = DocumentCollectorCallback()
callback_db['doc_collector'] = RE.subscribe(doc_collector.receiver)


# write scans to SPEC data file
specwriter = SpecWriterCallback()
# make the SPEC file in /tmp (assumes OS is Linux)
if os.getcwd().startswith("/home/beams/USAXS/.ipython"):
    specwriter.newfile(os.path.join("/tmp", specwriter.spec_filename))
else:
    specwriter.newfile(reset_scan_id=True, RE=RE)
callback_db['specwriter'] = RE.subscribe(specwriter.receiver)
print()
print("writing to SPEC file: " + specwriter.spec_filename)
print(">>>>   Using default SPEC file name   <<<<")
print("file will be created when bluesky ends its next scan")
print("to change SPEC file, use command: newSpecFile('title')")

"""
EXAMPLE:

    specwriter.newfile("01_26_bluesky.dat", reset_scan_id=True, RE=RE)
    specwriter.newfile()   # gets a default name: yyyymmdd-hhmmss.dat
    specwriter.newfile(reset_scan_id=True, RE=RE)   # also sets scan_id = 0
"""


def newSpecFile(title, reset_scan_id=True):
    """
    user choice of the SPEC file name
    
    cleans up title, prepends month and day and appends file extension
    """
    mmdd = str(datetime.datetime.now()).split()[0][5:].replace("-", "_")
    clean = cleanupText(title)
    fname = "%s_%s.dat" % (mmdd, clean)
    if os.path.exists(fname):
        print(f"file already exists: {fname}")
        user_data.spec_file.put(specwriter.spec_filename)
        print(">>>>   Using default SPEC file name   <<<<")
        
    else:
        specwriter.newfile(fname, reset_scan_id=reset_scan_id)
        msg = f"spec file: {specwriter.spec_filename}"
        logger.info(msg)
        user_data.spec_file.put(specwriter.spec_filename)
    print(f"SPEC file name : {specwriter.spec_filename}")
    print("file will be created when bluesky ends its next scan")
