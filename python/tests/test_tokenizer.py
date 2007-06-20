import os
import unittest
from support import simplejson, html5lib_test_files

#RELEASE remove
from tokenizer import HTMLTokenizer
import constants
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib.tokenizer import HTMLTokenizer
#from html5lib import constants
#END RELEASE

class TokenizerTestParser(object):
    def __init__(self, contentModelFlag, lastStartTag=None):
        self.tokenizer = HTMLTokenizer
        self._contentModelFlag = constants.contentModelFlags[contentModelFlag]
        self._lastStartTag = lastStartTag

    def parse(self, stream, encoding=None, innerHTML=False):
        tokenizer = self.tokenizer(stream, encoding)
        self.outputTokens = []

        tokenizer.contentModelFlag = self._contentModelFlag
        if self._lastStartTag is not None:
            tokenizer.currentToken = {"type": "startTag", 
                                      "name":self._lastStartTag}

        for token in tokenizer:
            getattr(self, 'process%s' % token["type"])(token)

        return self.outputTokens

    def processDoctype(self, token):
        self.outputTokens.append([u"DOCTYPE", token["name"], token["publicId"], token["systemId"], token["correct"]])

    def processStartTag(self, token):
        self.outputTokens.append([u"StartTag", token["name"], token["data"]])

    def processEmptyTag(self, token):
        if token["name"] not in constants.voidElements:
            self.outputTokens.append(u"ParseError")
        self.outputTokens.append([u"StartTag", token["name"], token["data"]])

    def processEndTag(self, token):
        if token["data"]:
            self.processParseError(None)
        self.outputTokens.append([u"EndTag", token["name"]])

    def processComment(self, token):
        self.outputTokens.append([u"Comment", token["data"]])

    def processSpaceCharacters(self, token):
        self.outputTokens.append([u"Character", token["data"]])
        self.processSpaceCharacters = self.processCharacters

    def processCharacters(self, token):
        self.outputTokens.append([u"Character", token["data"]])

    def processEOF(self, token):
        pass

    def processParseError(self, token):
        self.outputTokens.append(u"ParseError")

def concatenateCharacterTokens(tokens):
    outputTokens = []
    for token in tokens:
        if not "ParseError" in token and token[0] == "Character":
            if (outputTokens and not "ParseError" in outputTokens[-1] and
                outputTokens[-1][0] == "Character"):
                outputTokens[-1][1] += token[1]
            else:
                outputTokens.append(token)
        else:
            outputTokens.append(token)
    return outputTokens

def normalizeTokens(tokens):
    """ convert array of attributes to a dictionary """
    # TODO: convert tests to reflect arrays
    for token in tokens:
        if token[0] == 'StartTag':
            token[2] = dict(token[2][::-1])
    return tokens

def tokensMatch(expectedTokens, recievedTokens):
    """Test whether the test has passed or failed

    For brevity in the tests, the test has passed if the sequence of expected
    tokens appears anywhere in the sequence of returned tokens.
    """
    return expectedTokens == recievedTokens
    for i, token in enumerate(recievedTokens):
        if expectedTokens[0] == token:
            if (len(expectedTokens) <= len(recievedTokens[i:]) and
                recievedTokens[i:i+len(expectedTokens)]):
                return True
    return False


class TestCase(unittest.TestCase):
    def runTokenizerTest(self, test):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        output = concatenateCharacterTokens(test['output'])
        if 'lastStartTag' not in test:
            test['lastStartTag'] = None
        parser = TokenizerTestParser(test['contentModelFlag'], 
                                     test['lastStartTag'])
            
        tokens = normalizeTokens(parser.parse(test['input']))
        tokens = concatenateCharacterTokens(tokens)
        errorMsg = "\n".join(["\n\nContent Model Flag:",
                              test['contentModelFlag'] ,
                              "\nInput:", str(test['input']),
                              "\nExpected:", str(output),
                              "\nRecieved:", str(tokens)])
        self.assertEquals(tokensMatch(tokens, output), True, errorMsg)

def buildTestSuite():
    for filename in html5lib_test_files('tokenizer', '*.test'):
        tests = simplejson.load(file(filename))
        testName = os.path.basename(filename).replace(".test","")
        for index,test in enumerate(tests['tests']):
            if 'contentModelFlags' not in test:
                test["contentModelFlags"] = ["PCDATA"]
            for contentModelFlag in test["contentModelFlags"]:
                test["contentModelFlag"] = contentModelFlag
                def testFunc(self, test=test):
                    self.runTokenizerTest(test)
                testFunc.__doc__ = "\t".join([testName, test['description']])
                setattr(TestCase, 'test_%s_%d' % (testName, index), testFunc)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()