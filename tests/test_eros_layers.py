import pytest
import random
from eros_core.eros_layers import (
    Framing,
    Verification,
    Routing,
    CRCException,
)  # Make sure you import the correct module


def generate_random_data(length: int) -> bytes:
    return bytes([random.randint(0, 255) for _ in range(length)])


def test_framing():
    framing = Framing()
    test_data = generate_random_data(16)
    encoded_data = framing.pack(test_data)
    assert isinstance(encoded_data, bytes)
    unpacked_data = framing.unpack(encoded_data + encoded_data)  # Add null termination
    assert isinstance(unpacked_data, list)
    assert len(unpacked_data) == 2
    assert unpacked_data[0] == test_data


def test_verification():
    verification = Verification()
    # Random test packet of 256 bytes
    test_data = generate_random_data(16)
    encoded_data = verification.pack(test_data)
    assert isinstance(encoded_data, bytes)

    # Correct CRC case
    try:
        decoded_data = verification.unpack(encoded_data)
        assert decoded_data == test_data
    except ValueError:
        pytest.fail("Unexpected ValueError ..")

    # Incorrect CRC case
    with pytest.raises(CRCException):
        # Change the first byte of the encoded data to something else, guaranteed to be wrong
        encoded_data = encoded_data[1:]
        verification.unpack(encoded_data + b"\x00")  # Add unexpected data


def test_routing():
    routing = Routing()

    # Valid cases
    for channel in range(
        16
    ):  # As the channel is 4 bits it should accept values from 0 to 15
        for req_resp in [True, False]:
            for version in range(
                4
            ):  # As the version is 2 bits it should accept values from 0 to 3
                test_data = generate_random_data(16)
                packed_data = routing.pack(test_data, version, channel, req_resp)
                assert isinstance(packed_data, bytes)
                header, unpacked_data = routing.unpack(packed_data)
                assert unpacked_data == test_data
                assert header.version == version
                assert header.channel == channel
                assert header.request_response == req_resp
                assert header.reserved == 0

    # Invalid cases
    invalid_channels = [-1, 16, 20, 100, 1000]
    invalid_versions = [-1, 4, 5, 10, 20]
    for channel in invalid_channels:
        with pytest.raises(Exception):  # Expect exception due to invalid channel
            routing.pack(test_data, channel, True)
    for version in invalid_versions:
        with pytest.raises(Exception):  # Expect exception due to invalid version
            routing.pack(test_data, version, True)

    # Unpack with invalid data
    with pytest.raises(Exception):  # Expect exception due to invalid data length
        routing.unpack(b"")


if __name__ == "__main__":
    test_framing()
    test_verification()
    test_routing()
