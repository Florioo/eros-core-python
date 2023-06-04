import crc

class crc8_gen:
    def __init__(self) -> None:
        config = crc.Configuration(
            width=16,
            polynomial=0x07,
            init_value=0x00,
            final_xor_value=0x00,
            reverse_input=False,
            reverse_output=False,
        )
        self.calculator = crc.Calculator(config) 
        
    def get(self, data: bytes):
        return self.calculator.checksum(data).to_bytes(2,'big')
