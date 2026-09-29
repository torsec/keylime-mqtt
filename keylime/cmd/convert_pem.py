from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def tpmt_public_rsa_to_pem(data: bytes) -> str:
    """
    Converts a TPMT_PUBLIC RSA in hexadecimal format
    into a pubic key in PEM (SubjectPublicKeyInfo).

    Input:
        data = bytes from TPMT_PUBLIC in hex representation

    Output:
        -----BEGIN PUBLIC KEY-----
        ...
        -----END PUBLIC KEY-----
    """

    # data = bytes.fromhex(hex_string)
    print("\nData (in bytestring):\n")
    print(data)
    print("First two bytes: ", data[0], ", ", data[1], "\n")
    print("Third and Fourth byte are: ", data[2], ", ", data[3], "\n")

    pos = 0

    def read_u16():
        nonlocal pos
        value = int.from_bytes(data[pos:pos + 2], "big")
        pos += 2
        return value

    def read_u32():
        nonlocal pos
        value = int.from_bytes(data[pos:pos + 4], "big")
        pos += 4
        return value

    def read_tpm2b():
        nonlocal pos
        size = read_u16()
        print("Il size e': ", size, "\n")
        value = data[pos:pos + size]
        pos += size
        return value
    
    declared_size = int.from_bytes(data[0:2], "big")
    print("The declared size e': ", declared_size, "\n")
    data = data[2:]  # Skipping the first two bytes (size) and reading the rest of the TPMT_PUBLIC data structure

    # TPMT_PUBLIC
    # ----------------------------

    # type: TPM_ALG_RSA = 0x0001
    public_type = read_u16()
    print("\nThe public_type (in bytestring):\n")
    print(public_type)

    if public_type != 0x0001:
        raise ValueError(
            f"TPMT_PUBLIC non RSA: type=0x{public_type:04x}"
        )

    # nameAlg
    name_alg = read_u16()

    # objectAttributes
    object_attributes = read_u32()

    # authPolicy (TPM2B_DIGEST)
    auth_policy = read_tpm2b()

    # ----------------------------
    # TPMS_RSA_PARMS
    # ----------------------------

    # TPMT_SYM_DEF_OBJECT
    symmetric_alg = read_u16()

    if symmetric_alg != 0x0010:  # TPM_ALG_NULL
        # keyBits
        read_u16()

        # mode
        read_u16()

    # TPMT_RSA_SCHEME
    scheme = read_u16()

    # Schemes which contain a hashAlg
    # RSASSA = 0x0014
    # RSAES  = 0x0015
    # RSAPSS = 0x0016
    # OAEP   = 0x0017
    if scheme in (0x0014, 0x0015, 0x0016, 0x0017):
        read_u16()  # hashAlg

    # keyBits
    key_bits = read_u16()

    # exponent
    exponent = read_u32()

    # TPM2B_PUBLIC_KEY_RSA
    modulus = read_tpm2b()

    if key_bits != 2048:
        raise ValueError(
            f"The RSA key does not have 2048 bit: keyBits={key_bits}"
        )

    if len(modulus) != 256:
        raise ValueError(
            f"Unexpected modulus: {len(modulus)} bytes, 256 expected"
        )

    # TPM convention:
    # exponent == 0 means 2^16 + 1 = 65537
    if exponent == 0:
        exponent = 65537

    # Costruisce la chiave RSA
    public_key = rsa.RSAPublicNumbers(
        e=exponent,
        n=int.from_bytes(modulus, "big")
    ).public_key()

    # PEM SubjectPublicKeyInfo
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return pem.decode("ascii")