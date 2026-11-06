import hashlib
import uuid

class MSK_HexIndex(str):
    def __new__(cls, 
                value: str | None=None, 
                do_make: bool=False):
        if do_make:
            if value is not None:
                value = f"0x{hashlib.md5(value.encode('utf-8')).hexdigest()}"
            else:
                value = f"0x{uuid.uuid4().hex}"

        if value is None:
            return super().__new__(cls, "0x00000000000000000000000000000000")
        
        if not isinstance(value, str):
            raise TypeError("MSK_HexIndex must be a Python str based object")
        
        if not value.startswith("0x"):
            raise ValueError("MSK_HexIndex must start with '0x'")
        
        hex_part = value[2:]
        if len(hex_part) != 32:
            raise ValueError("MSK_HexIndex must be a hexadecimal representation of a 128-bit binary")
        
        try:
            num = int(value, 16)
        except ValueError:
            raise ValueError("Invalid hexadecimal value")
        
        if not (0 <= num < 2**128):
            raise ValueError("Value exceeding")
        
        return super().__new__(cls, value)

    def __repr__(self):
        return f"MSK_HexIndex('{self}')"

    def to_bytes(self):
        bytes_rep = bytes.fromhex(self[2:])
        return bytes_rep