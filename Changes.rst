Version 0.5.0 (2016-03-02)
--------------------------
- Add support for using a KeyName element within the KeyInfo block (#38). Thanks to @Pelleplutt.
- Update cryptography dependency
- Expand Travis CI test matrix to include OS X

Version 0.4.6 (2015-11-28)
--------------------------
- Python 3.5 compatibility fix: move enum34 into conditional dependencies (#37). Thanks to @agronholm.

Version 0.4.5 (2015-11-08)
--------------------------
- Support enveloped signatures nested at arbitrary levels beneath root element (#32, #33). Thanks to @jmindek.
- Update certifi, cryptography dependencies

Version 0.4.4 (2015-08-07)
--------------------------
- Handle xml.etree.ElementTree nodes as input (previously these would cause a crash, despite the documentation suggesting otherwise). Closes #19, thanks to @nickcash.

Version 0.4.3 (2015-07-26)
--------------------------
- Do not open schema file in text mode when parsing XML (closes #18, thanks to @nick210)
- Update cryptography dependency

Version 0.4.2 (2015-04-24)
--------------------------
- Add support for parameterizable signature namespace (PR #12, thanks to @ldnunes)
- Update cryptography dependency

Version 0.4.1 (2015-04-21)
--------------------------
- Add support for detached signatures (closes #3)
- Update pyOpenSSL dependency; use X509StoreContext.verify_certificate()

Version 0.4.0 (2015-03-08)
--------------------------
- Use pyasn1 for DER encoding and decoding, eliminating some DSA signature verification failures

Version 0.3.9 (2015-02-04)
--------------------------
- Do not distribute tests in source archive

Version 0.3.7 (2015-02-04)
--------------------------
- Configurable id attribute name for verifying non-standard internal object references, e.g. ADFS (closes #6)

Version 0.3.6 (2015-01-10)
--------------------------
- Python 3 compatibility fixes
- Fix test matrix (Python version configuration) in Travis

Version 0.3.5 (2014-12-22)
--------------------------
- Refactor application of enveloped signature transforms
- Support base64 transform
- Support application of different canonicalization algorithms to signature and payload (closes #1)

Version 0.3.4 (2014-12-14)
--------------------------
- Add support for exclusive canonicalization with InclusiveNamespaces PrefixList attribute

Version 0.3.3 (2014-12-13)
--------------------------
- Overhaul support of canonicalization algorithms

Version 0.3.2 (2014-12-11)
--------------------------
- Fix bug in enveloped signature canonicalization of namespace prefixes

Version 0.3.1 (2014-10-17)
--------------------------
- Fix bug in enveloped signature excision

Version 0.3.0 (2014-10-16)
--------------------------
- Allow location of enveloped signature to be specified

Version 0.2.9 (2014-10-14)
--------------------------
- Use exclusive c14n when signing

Version 0.2.8 (2014-10-13)
--------------------------
- Namespace all tags when generating signature

Version 0.2.7 (2014-10-13)
--------------------------
- Switch default signing method to enveloped signature

Version 0.2.6 (2014-10-13)
--------------------------
- Fix typo in ns prefixing code

Version 0.2.5 (2014-10-13)
--------------------------
- Fix handling of DER sequences in DSA key serialization
- Parameterize excision with ns prefix

Version 0.2.4 (2014-10-12)
--------------------------
- Fix excision with ns prefix

Version 0.2.3 (2014-10-12)
--------------------------
- Fixes to c14n of enveloped signatures
- Expand tests to use the XML Signature interoperability test suite

Version 0.2.2 (2014-10-04)
--------------------------
- Load bare X509 certificates from SAML metadata correctly

Version 0.2.1 (2014-10-04)
--------------------------
- Always use X509 information even if key value is present
- Internal refactor to modularize key value handling logic

Version 0.2.0 (2014-10-02)
--------------------------
- Use defusedxml when verifying signatures.
- Eliminate dependency on PyCrypto.
- Introduce support for ECDSA asymmetric key encryption.
- Introduce ability to validate xmldsig11 schema.
- Expand test suite coverage.

Version 0.1.9 (2014-09-27)
--------------------------
- Allow use of external X509 certificates for validation; add an example of supplying a cert from SAML metadata.

Version 0.1.8 (2014-09-25)
--------------------------
- Packaging fix.

Version 0.1.7 (2014-09-25)
--------------------------
- Packaging fix.

Version 0.1.6 (2014-09-25)
--------------------------
- Accept etree elements in verify.

Version 0.1.5 (2014-09-25)
--------------------------
- Packaging fix.

Version 0.1.4 (2014-09-25)
--------------------------
- Begin work toward conformance with version 1.1 of the spec.

Version 0.1.3 (2014-09-23)
--------------------------
- Require x509 for verification by default.

Version 0.1.2 (2014-09-22)
--------------------------
- Documentation fixes.

Version 0.1.1 (2014-09-22)
--------------------------
- Documentation fixes.

Version 0.1.0 (2014-09-22)
--------------------------
- Initial release.
