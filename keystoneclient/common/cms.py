import hashlib

import logging


subprocess = None
LOG = logging.getLogger(__name__)
PKI_ANS1_PREFIX = 'MII'


def _ensure_subprocess():
    # NOTE(vish): late loading subprocess so we can
    #             use the green version if we are in
    #             eventlet.
    global subprocess
    if not subprocess:
        try:
            from eventlet import patcher
            if patcher.already_patched.get('os'):
                from eventlet.green import subprocess
            else:
                import subprocess
        except ImportError:
            import subprocess


def cms_verify(formatted, signing_cert_file_name, ca_file_name):
    """
        verifies the signature of the contents IAW CMS syntax
    """
    _ensure_subprocess()
    process = subprocess.Popen(["openssl", "cms", "-verify",
                                "-certfile", signing_cert_file_name,
                                "-CAfile", ca_file_name,
                                "-inform", "PEM",
                                "-nosmimecap", "-nodetach",
                                "-nocerts", "-noattr"],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, err = process.communicate(formatted)
    retcode = process.poll()
    if retcode:
        LOG.error('Verify error: %s' % err)
        # NOTE(dmllr): Python 2.6 compatibility:
        # CalledProcessError did not have output keyword argument
        e = subprocess.CalledProcessError(retcode, "openssl")
        e.output = err
        raise e
    return output


def token_to_cms(signed_text):
    copy_of_text = signed_text.replace('-', '/')

    formatted = "-----BEGIN CMS-----\n"
    line_length = 64
    while len(copy_of_text) > 0:
        if (len(copy_of_text) > line_length):
            formatted += copy_of_text[:line_length]
            copy_of_text = copy_of_text[line_length:]
        else:
            formatted += copy_of_text
            copy_of_text = ""
        formatted += "\n"

    formatted += "-----END CMS-----\n"

    return formatted


def verify_token(token, signing_cert_file_name, ca_file_name):
    return cms_verify(token_to_cms(token),
                      signing_cert_file_name,
                      ca_file_name)


def is_ans1_token(token):
    '''
    thx to ayoung for sorting this out.

    base64 decoded hex representation of MII is 3082
    In [3]: binascii.hexlify(base64.b64decode('MII='))
    Out[3]: '3082'

    re: http://www.itu.int/ITU-T/studygroups/com17/languages/X.690-0207.pdf

    pg4:  For tags from 0 to 30 the first octet is the identfier
    pg10: Hex 30 means sequence, followed by the length of that sequence.
    pg5:  Second octet is the length octet
          first bit indicates short or long form, next 7 bits encode the number
          of subsequent octets that make up the content length octets as an
          unsigned binary int

          82 = 10000010 (first bit indicates long form)
          0000010 = 2 octets of content length
          so read the next 2 octets to get the length of the content.

    In the case of a very large content length there could be a requirement to
    have more than 2 octets to designate the content length, therefore
    requiring us to check for MIM, MIQ, etc.
    In [4]: base64.b64encode(binascii.a2b_hex('3083'))
    Out[4]: 'MIM='
    In [5]: base64.b64encode(binascii.a2b_hex('3084'))
    Out[5]: 'MIQ='
    Checking for MI would become invalid at 16 octets of content length
    10010000 = 90
    In [6]: base64.b64encode(binascii.a2b_hex('3090'))
    Out[6]: 'MJA='
    Checking for just M is insufficient

    But we will only check for MII:
    Max length of the content using 2 octets is 7FFF or 32767
    It's not practical to support a token of this length or greater in http
    therefore, we will check for MII only and ignore the case of larger tokens
    '''
    return token[:3] == PKI_ANS1_PREFIX


def cms_sign_text(text, signing_cert_file_name, signing_key_file_name):
    """ Uses OpenSSL to sign a document
    Produces a Base64 encoding of a DER formatted CMS Document
    http://en.wikipedia.org/wiki/Cryptographic_Message_Syntax
    """
    _ensure_subprocess()
    process = subprocess.Popen(["openssl", "cms", "-sign",
                                "-signer", signing_cert_file_name,
                                "-inkey", signing_key_file_name,
                                "-outform", "PEM",
                                "-nosmimecap", "-nodetach",
                                "-nocerts", "-noattr"],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, err = process.communicate(text)
    retcode = process.poll()
    if retcode or "Error" in err:
        LOG.error('Signing error: %s' % err)
        raise subprocess.CalledProcessError(retcode, "openssl")
    return output


def cms_sign_token(text, signing_cert_file_name, signing_key_file_name):
    output = cms_sign_text(text, signing_cert_file_name, signing_key_file_name)
    return cms_to_token(output)


def cms_to_token(cms_text):

    start_delim = "-----BEGIN CMS-----"
    end_delim = "-----END CMS-----"
    signed_text = cms_text
    signed_text = signed_text.replace('/', '-')
    signed_text = signed_text.replace(start_delim, '')
    signed_text = signed_text.replace(end_delim, '')
    signed_text = signed_text.replace('\n', '')

    return signed_text


def cms_hash_token(token_id):
    """
    return: for ans1_token, returns the hash of the passed in token
            otherwise, returns what it was passed in.
    """
    if token_id is None:
        return None
    if is_ans1_token(token_id):
        hasher = hashlib.md5()
        hasher.update(token_id)
        return hasher.hexdigest()
    else:
        return token_id
