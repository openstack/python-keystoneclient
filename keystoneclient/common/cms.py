#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Certificate signing functions.

Call set_subprocess() with the subprocess module. Either Python's
subprocess or eventlet.green.subprocess can be used.

If set_subprocess() is not called, this module will pick Python's subprocess
or eventlet.green.subprocess based on if os module is patched by eventlet.
"""

import errno
import hashlib
import logging
import six

from keystoneclient import exceptions


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
            if patcher.already_patched:
                from eventlet.green import subprocess
            else:
                import subprocess
        except ImportError:
            import subprocess  # noqa


def set_subprocess(_subprocess=None):
    """Set subprocess module to use.
    The subprocess could be eventlet.green.subprocess if using eventlet,
    or Python's subprocess otherwise.
    """
    global subprocess
    subprocess = _subprocess


def _check_files_accessible(files):
    err = None
    try:
        for try_file in files:
            with open(try_file, 'r'):
                pass
    except IOError as e:
        # Catching IOError means there is an issue with
        # the given file.
        err = ('Hit OSError in _process_communicate_handle_oserror()\n'
               'Likely due to %s: %s') % (try_file, e.strerror)

    return err


def _process_communicate_handle_oserror(process, text, files):
    """Wrapper around process.communicate that checks for OSError."""

    try:
        output, err = process.communicate(text)
    except OSError as e:
        if e.errno != errno.EPIPE:
            raise
        # OSError with EPIPE only occurs with Python 2.6.x/old 2.7.x
        # http://bugs.python.org/issue10963

        # The quick exit is typically caused by the openssl command not being
        # able to read an input file, so check ourselves if can't read a file.
        err = _check_files_accessible(files)
        if process.stderr:
            err += process.stderr.read()

        output = ""
        retcode = -1
    else:
        retcode = process.poll()

    return output, err, retcode


def cms_verify(formatted, signing_cert_file_name, ca_file_name):
    """Verifies the signature of the contents IAW CMS syntax.

    :raises: subprocess.CalledProcessError
    :raises: CertificateConfigError if certificate is not configured properly.
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
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    output, err, retcode = _process_communicate_handle_oserror(
        process, formatted, (signing_cert_file_name, ca_file_name))

    # Do not log errors, as some happen in the positive thread
    # instead, catch them in the calling code and log them there.

    # When invoke the openssl with not exist file, return code 2
    # and error msg will be returned.
    # You can get more from
    # http://www.openssl.org/docs/apps/cms.html#EXIT_CODES
    #
    # $ openssl cms -verify -certfile not_exist_file -CAfile \
    #       not_exist_file -inform PEM -nosmimecap -nodetach \
    #       -nocerts -noattr
    # Error opening certificate file not_exist_file
    #
    if retcode == 2:
        raise exceptions.CertificateConfigError(err)
    elif retcode:
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
    """Determine if a token appears to be PKI-based.

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
    """
    return token[:3] == PKI_ANS1_PREFIX


def cms_sign_text(text, signing_cert_file_name, signing_key_file_name):
    """Uses OpenSSL to sign a document.

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
                               stderr=subprocess.PIPE,
                               universal_newlines=True)

    output, err, retcode = _process_communicate_handle_oserror(
        process, text, (signing_cert_file_name, signing_key_file_name))

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
    """Hash PKI tokens.

    return: for ans1_token, returns the hash of the passed in token
            otherwise, returns what it was passed in.
    """
    if token_id is None:
        return None
    if is_ans1_token(token_id):
        hasher = hashlib.md5()
        if isinstance(token_id, six.text_type):
            token_id = token_id.encode('utf-8')
        hasher.update(token_id)
        return hasher.hexdigest()
    else:
        return token_id
