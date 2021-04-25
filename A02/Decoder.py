class Decoder:

    def __init__(self):
        pass

    def __call__(self,encoded_stream,path = None):

        self.decode(encoded_stream)

        if(path is not None):
            self.write_file(path)

        return self.decoded_data

    def write_file(self,path,decoded_data=None):

        if(decoded_data is not None):
            self.decoded_data=decoded_data

        file = open(path, "wb")
        file.write(self.decoded_data)
        return True

    def decode(self,encoded_stream):

        # actual decoding
        self.decoded_data=encoded_stream
        return self.decoded_data