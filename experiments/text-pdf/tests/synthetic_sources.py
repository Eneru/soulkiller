"""Reusable synthetic inputs; no captured or personal source data."""

BILINGUAL_TEXT = "Je suis Inez.\r\nI remember Corin.\nÉté : café, e\u0301, \U0001f31f.\x00"
BILINGUAL_BYTES = BILINGUAL_TEXT.encode("utf-8")
BILINGUAL_SHA256 = "ab1ff63873d17ab432ac1019a4fdac46360ced7b2f7688959feac40f5ff2de33"

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
INVALID_BYTES = b"\xff"
INVALID_SHA256 = "a8100ae6aa1940d0b663bb31cd466142ebbdbd5187131b92d93818987832eb89"

CODEPOINT_TEXT = "Aé e\u0301\U0001f31fZ"
