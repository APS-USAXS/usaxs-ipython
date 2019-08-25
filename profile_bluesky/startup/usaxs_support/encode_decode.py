
"""
conversion to utf-8 and from others

:see: https://stackoverflow.com/questions/447107/what-is-the-difference-between-encode-decode
"""


from reportlab.lib.utils import asUnicode



XML_CODEPOINT = 'ISO-8859-1'
CODEPOINT_LIST = ('utf8 ascii utf16 utf32'.split()
                  + ['cp125'+str(i) for i in range(9)]
                  + ['latin'+str(i+1) for i in range(10)])

def text_decode(source):
    """
    try decoding ``source`` with various known codepoints to unicode

    for more information on the various codepoints, see
    https://docs.python.org/2/library/codecs.html#standard-encodings
    
    :see: https://github.com/prjemian/assign_gup/issues/55
    :see: http://stackoverflow.com/questions/9942594/unicodeencodeerror-ascii-codec-cant-encode-character-u-xa0-in-position-20
    """
    return asUnicode(source)

# from reportlab.lib.utils import asUnicode # sorts out py2 or py3
#     def asUnicode(v,enc='utf8'):
#         return v if isinstance(v,unicode) else v.decode(enc)

    # for encoding in CODEPOINT_LIST:  # walk through a list of codepoints
    #     print encoding
    #     try:
    #         return source.decode(encoding, 'replace')
    #     except (ValueError, UnicodeError) as _exc:
    #         continue
    #     except Exception as _exc:
    #         continue
    # return source


def text_encode(source):
    """
    encode ``source`` using the default codepoint
    """
    return source.encode(errors='ignore')


def to_unicode_or_bust(obj, encoding='utf-8'):
    """from: http://farmdev.com/talks/unicode/"""
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj
