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

import base64
import errno
import hashlib
import logging
import zlib

from debtcollector import removals
import six

from keystoneclient import exceptions
from keystoneclient.i18n import _


subprocess = None
LOG = logging.getLogger(__name__)
PKI_ASN1_PREFIX = 'MII'
PKIZ_PREFIX = 'PKIZ_'
PKIZ_CMS_FORM = 'DER'
PKI_ASN1_FORM = 'PEM'
DEFAULT_TOKEN_DIGEST_ALGORITHM = 'sha256'


# The openssl cms command exits with these status codes.
# See https://www.openssl.org/docs/man1.1.0/apps/cms.html#EXIT-CODES
class OpensslCmsExitStatus(object):
    SUCCESS = 0
    COMMAND_OPTIONS_PARSING_ERROR = 1
    INPUT_FILE_READ_ERROR = 2
    CREATE_CMS_READ_MIME_ERROR = 3


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
                import subprocess  # nosec(cjschaef): we must be careful when
                # using subprocess.Popen with possibly untrusted data,
                # assumption is that the certificate/key files provided are
                # trustworthy
        except ImportError:
            import subprocess  # noqa # nosec(cjschaef): we must be careful
            # when using subprocess.Popen with possibly untrusted data,
            # assumption is that the certificate/key files provided are
            # trustworthy


def set_subprocess(_subprocess=None):
    """Set subprocess module to use.

    The subprocess could be eventlet.green.subprocess if using eventlet,
    or Python's subprocess otherwise.
    """
    global subprocess
    subprocess = _subprocess


def _check_files_accessible(files):
    err = None
    retcode = -1
    try:
        for try_file in files:
            with open(try_file, 'r'):
                pass
    except IOError as e:
        # Catching IOError means there is an issue with
        # the given file.
        err = try_file, e.strerror
        # Emulate openssl behavior, which returns with code 2 when
        # access to a file failed.
        retcode = OpensslCmsExitStatus.INPUT_FILE_READ_ERROR

    return retcode, err


def _process_communicate_handle_oserror(process, data, files):
    """Wrapper around process.communicate that checks for OSError."""
    try:
        output, err = process.communicate(data)
    except OSError as e:
        if e.errno != errno.EPIPE:
            raise
        # OSError with EPIPE only occurs with old Python 2.7.x versions
        # http://bugs.python.org/issue10963

        # The quick exit is typically caused by the openssl command not being
        # able to read an input file, so check ourselves if can't read a file.
        retcode, err = _check_files_accessible(files)
        if process.stderr:
            msg = process.stderr.read()
            if isinstance(msg, six.binary_type):
                msg = msg.decode('utf-8')
            if err:
                err = (_('Hit OSError in '
                         '_process_communicate_handle_oserror(): '
                         '%(stderr)s\nLikely due to %(file)s: %(error)s') %
                       {'stderr': msg,
                        'file': err[0],
                        'error': err[1]})
            else:
                err = (_('Hit OSError in '
                         '_process_communicate_handle_oserror(): %s') % msg)

        output = ''
    else:
        retcode = process.poll()
        if err is not None:
            if isinstance(err, six.binary_type):
                err = err.decode('utf-8')

    return output, err, retcode


def _encoding_for_form(inform):
    if inform == PKI_ASN1_FORM:
        encoding = 'UTF-8'
    elif inform == PKIZ_CMS_FORM:
        encoding = 'hex'
    else:
        raise ValueError(
            _('"inform" must be one of: %s') % ','.join((PKI_ASN1_FORM,
                                                         PKIZ_CMS_FORM)))

    return encoding


def cms_verify(formatted, signing_cert_file_name, ca_file_name,
               inform=PKI_ASN1_FORM):
    """Verify the signature of the contents IAW CMS syntax.

    :raises subprocess.CalledProcessError:
    :raises keystoneclient.exceptions.CertificateConfigError: if certificate
                                                              is not configured
                                                              properly.
    """
    _ensure_subprocess()
    if isinstance(formatted, six.string_types):
        data = bytearray(formatted, _encoding_for_form(inform))
    else:
        data = formatted
    process = subprocess.Popen(['openssl', 'cms', '-verify',
                                '-certfile', signing_cert_file_name,
                                '-CAfile', ca_file_name,
                                '-inform', 'PEM',
                                '-nosmimecap', '-nodetach',
                                '-nocerts', '-noattr'],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
    output, err, retcode = _process_communicate_handle_oserror(
        process, data, (signing_cert_file_name, ca_file_name))

    # Do not log errors, as some happen in the positive thread
    # instead, catch them in the calling code and log them there.

    # When invoke the openssl >= 1.1.0 with not exist file, return code should
    # be 2 instead of 1 and error msg will be returned.
    # You can get more from
    # https://www.openssl.org/docs/man1.1.0/apps/cms.html#EXIT-CODES
    #
    # $ openssl cms -verify -certfile not_exist_file -CAfile
    #       not_exist_file -inform PEM -nosmimecap -nodetach
    #       -nocerts -noattr
    # openssl < 1.1.0 returns
    # Error opening certificate file not_exist_file
    # openssl >= 1.1.0 returns
    # cms: Cannot open input file not_exist_file, No such file or directory
    #
    if retcode == OpensslCmsExitStatus.INPUT_FILE_READ_ERROR:
        if err.startswith('Error reading S/MIME message'):
            raise exceptions.CMSError(err)
        else:
            raise exceptions.CertificateConfigError(err)
    # workaround for OpenSSL >= 1.1.0,
    # should return OpensslCmsExitStatus.INPUT_FILE_READ_ERROR
    elif retcode == OpensslCmsExitStatus.COMMAND_OPTIONS_PARSING_ERROR:
        if err.startswith('cms: Cannot open input file'):
            raise exceptions.CertificateConfigError(err)
        else:
            raise subprocess.CalledProcessError(retcode, 'openssl', output=err)
    elif retcode != OpensslCmsExitStatus.SUCCESS:
        raise subprocess.CalledProcessError(retcode, 'openssl', output=err)
    return output


def is_pkiz(token_text):
    """Determine if a token is PKIZ.

    Checks if the string has the prefix that indicates it is a
    Crypto Message Syntax, Z compressed token.
    """
    return token_text.startswith(PKIZ_PREFIX)


def pkiz_sign(text,
              signing_cert_file_name,
              signing_key_file_name,
              compression_level=6,
              message_digest=DEFAULT_TOKEN_DIGEST_ALGORITHM):
    signed = cms_sign_data(text,
                           signing_cert_file_name,
                           signing_key_file_name,
                           PKIZ_CMS_FORM,
                           message_digest=message_digest)

    compressed = zlib.compress(signed, compression_level)
    encoded = PKIZ_PREFIX + base64.urlsafe_b64encode(
        compressed).decode('utf-8')
    return encoded


def pkiz_uncompress(signed_text):
    text = signed_text[len(PKIZ_PREFIX):].encode('utf-8')
    unencoded = base64.urlsafe_b64decode(text)
    uncompressed = zlib.decompress(unencoded)
    return uncompressed


def pkiz_verify(signed_text, signing_cert_file_name, ca_file_name):
    uncompressed = pkiz_uncompress(signed_text)
    return cms_verify(uncompressed, signing_cert_file_name, ca_file_name,
                      inform=PKIZ_CMS_FORM)


def token_to_cms(signed_text):
    """Convert a custom formatted token to a PEM-formatted token.

    See documentation for cms_to_token() for details on the custom formatting.
    """
    copy_of_text = signed_text.replace('-', '/')

    lines = ['-----BEGIN CMS-----']
    lines += [copy_of_text[n:n + 64] for n in range(0, len(copy_of_text), 64)]
    lines.append('-----END CMS-----\n')
    return '\n'.join(lines)


def verify_token(token, signing_cert_file_name, ca_file_name):
    return cms_verify(token_to_cms(token),
                      signing_cert_file_name,
                      ca_file_name)


def is_asn1_token(token):
    """Determine if a token appears to be PKI-based.

    thx to ayoung for sorting this out.

    base64 decoded hex representation of MII is 3082::

      In [3]: binascii.hexlify(base64.b64decode('MII='))
      Out[3]: '3082'

    re: http://www.itu.int/ITU-T/studygroups/com17/languages/X.690-0207.pdf

    ::

      pg4:  For tags from 0 to 30 the first octet is the identfier
      pg10: Hex 30 means sequence, followed by the length of that sequence.
      pg5:  Second octet is the length octet
            first bit indicates short or long form, next 7 bits encode the
            number of subsequent octets that make up the content length octets
            as an unsigned binary int

            82 = 10000010 (first bit indicates long form)
            0000010 = 2 octets of content length
            so read the next 2 octets to get the length of the content.

    In the case of a very large content length there could be a requirement to
    have more than 2 octets to designate the content length, therefore
    requiring us to check for MIM, MIQ, etc.

    ::

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
    Max length of the content using 2 octets is 3FFF or 16383.

    It's not practical to support a token of this length or greater in http
    therefore, we will check for MII only and ignore the case of larger tokens
    """
    return token[:3] == PKI_ASN1_PREFIX


@removals.remove(message='Use is_asn1_token() instead.', version='1.7.0',
                 removal_version='2.0.0')
def is_ans1_token(token):
    """Deprecated.

    This function is deprecated as of the 1.7.0 release in favor of
    :func:`is_asn1_token` and may be removed in the 2.0.0 release.
    """
    return is_asn1_token(token)


def cms_sign_text(data_to_sign, signing_cert_file_name, signing_key_file_name,
                  message_digest=DEFAULT_TOKEN_DIGEST_ALGORITHM):
    return cms_sign_data(data_to_sign, signing_cert_file_name,
                         signing_key_file_name, message_digest=message_digest)


def cms_sign_data(data_to_sign, signing_cert_file_name, signing_key_file_name,
                  outform=PKI_ASN1_FORM,
                  message_digest=DEFAULT_TOKEN_DIGEST_ALGORITHM):
    """Use OpenSSL to sign a document.

    Produces a Base64 encoding of a DER formatted CMS Document
    http://en.wikipedia.org/wiki/Cryptographic_Message_Syntax

    :param data_to_sign: data to sign
    :param signing_cert_file_name:  path to the X509 certificate containing
        the public key associated with the private key used to sign the data
    :param signing_key_file_name: path to the private key used to sign
        the data
    :param outform: Format for the signed document PKIZ_CMS_FORM or
        PKI_ASN1_FORM
    :param message_digest: Digest algorithm to use when signing or resigning

    """
    _ensure_subprocess()
    if isinstance(data_to_sign, six.string_types):
        data = bytearray(data_to_sign, encoding='utf-8')
    else:
        data = data_to_sign
    process = subprocess.Popen(['openssl', 'cms', '-sign',
                                '-signer', signing_cert_file_name,
                                '-inkey', signing_key_file_name,
                                '-outform', 'PEM',
                                '-nosmimecap', '-nodetach',
                                '-nocerts', '-noattr',
                                '-md', message_digest, ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)

    output, err, retcode = _process_communicate_handle_oserror(
        process, data, (signing_cert_file_name, signing_key_file_name))

    if retcode != OpensslCmsExitStatus.SUCCESS or ('Error' in err):
        if retcode == OpensslCmsExitStatus.CREATE_CMS_READ_MIME_ERROR:
            LOG.error('Signing error: Unable to load certificate - '
                      'ensure you have configured PKI with '
                      '"keystone-manage pki_setup"')
        else:
            LOG.error('Signing error: %s', err)
        raise subprocess.CalledProcessError(retcode, 'openssl')
    if outform == PKI_ASN1_FORM:
        return output.decode('utf-8')
    else:
        return output


def cms_sign_token(text, signing_cert_file_name, signing_key_file_name,
                   message_digest=DEFAULT_TOKEN_DIGEST_ALGORITHM):
    output = cms_sign_data(text, signing_cert_file_name, signing_key_file_name,
                           message_digest=message_digest)
    return cms_to_token(output)


def cms_to_token(cms_text):
    """Convert a CMS-signed token in PEM format to a custom URL-safe format.

    The conversion consists of replacing '/' char in the PEM-formatted token
    with the '-' char and doing other such textual replacements to make the
    result marshallable via HTTP. The return value can thus be used as the
    value of a HTTP header such as "X-Auth-Token".

    This ad-hoc conversion is an unfortunate oversight since the returned
    value now does not conform to any of the standard variants of base64
    encoding. It would have been better to use base64url encoding (either on
    the PEM formatted text or, perhaps even better, on the inner CMS-signed
    binary value without any PEM formatting). In any case, the same conversion
    is done in reverse in the other direction (for token verification), so
    there are no correctness issues here. Note that the non-standard encoding
    of the token will be preserved so as to not break backward compatibility.

    The conversion issue is detailed by the code author in a blog post at
    http://adam.younglogic.com/2014/02/compressed-tokens/.
    """
    start_delim = '-----BEGIN CMS-----'
    end_delim = '-----END CMS-----'
    signed_text = cms_text
    signed_text = signed_text.replace('/', '-')
    signed_text = signed_text.replace(start_delim, '')
    signed_text = signed_text.replace(end_delim, '')
    signed_text = signed_text.replace('\n', '')

    return signed_text


def cms_hash_token(token_id, mode='md5'):
    """Hash PKI tokens.

    return: for asn1 or pkiz tokens, returns the hash of the passed in token
            otherwise, returns what it was passed in.
    """
    if token_id is None:
        return None
    if is_asn1_token(token_id) or is_pkiz(token_id):
        hasher = hashlib.new(mode)
        if isinstance(token_id, six.text_type):
            token_id = token_id.encode('utf-8')
        hasher.update(token_id)
        return hasher.hexdigest()
    else:
        return token_id
