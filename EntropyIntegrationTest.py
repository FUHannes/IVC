from EntropyDecoder import EntropyDecoder
from EntropyEncoder import EntropyEncoder
from OBitstream import OBitstream
from IBitstream import IBitstream
import tempfile


def test_entropy_integration_test():
    path = tempfile.mkstemp()[1]
    stream = OBitstream(path)
    encoder = EntropyEncoder(stream)
    for val in range(-10, 11):
        encoder.writeQIndex(val)
    stream.terminate()

    stream = IBitstream(path)
    for val in range(-10, 11):
        decoder = EntropyDecoder(stream)
        read_val = decoder.readQIndex()

        assert val == read_val
