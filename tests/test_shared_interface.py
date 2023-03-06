from time import sleep

from programmor_adapters.shared.comm import Comm, Frame, FRAME_PAYLOAD_SIZE, ProcessState


# Fake comms interface
class Connection(Comm):
    def __init__(self) -> None:
        super().__init__()
        self.incoming_buffer: bytearray = bytearray()
        self.outgoing_buffer: bytearray = bytearray()

    def read(self) -> bytes:
        # Return no bytes if device is not ready
        return self.incoming_buffer

    def write(self, buffer: bytes) -> None:
        self.outgoing_buffer.extend(buffer)

    def close(self) -> None:
        self.outgoing_buffer.clear()
        self.incoming_buffer.clear()


def generate_frame(fromRange: int = 0, toRange: int = FRAME_PAYLOAD_SIZE) -> Frame:
    in_data = Frame()
    in_data.destinationAddress = 0x01
    in_data.payload = bytes([x for x in range(fromRange, toRange)])
    return in_data


def test_initilise_comms():
    com = Connection()
    assert isinstance(com, Connection)


def test_initilise_frame():
    frame = Frame()
    assert frame.preamble == 0x01
    assert type(frame.to_bytes()) is bytearray


def test_frame_to_bytes_then_from_bytes():
    # Generate frame
    frame = Frame()
    frame.preamble = 0x02
    frame.destinationAddress = 0x03
    frame.sourceAddress = 0x04
    frame.frameId = 5
    frame.frameOrder = 1
    frame.frameTotal = 1
    frame.payload = bytes([x for x in range(FRAME_PAYLOAD_SIZE)])
    frame.calculate_crc()
    # Generate bytes
    frame_as_bytes = frame.to_bytes()
    # Unpack an see if the reuslt is correct
    from_frame = Frame(frame_as_bytes)
    # Check result
    assert from_frame.is_valid() is True
    assert from_frame.preamble == frame.preamble
    assert from_frame.destinationAddress == frame.destinationAddress
    assert from_frame.sourceAddress == frame.sourceAddress
    assert from_frame.frameId == frame.frameId
    assert from_frame.frameOrder == frame.frameOrder
    assert from_frame.frameTotal == frame.frameTotal
    assert from_frame.payload == frame.payload


def test_comms_read_single_frame():
    # Call back on successful message
    def on_received_message(message: bytes):
        assert message == bytes([x for x in range(FRAME_PAYLOAD_SIZE)])

    com = Connection()
    com.set_received_message_callback(on_received_message)
    # Test data
    in_data = generate_frame()
    com.incoming_buffer = in_data.to_bytes()
    # Test read function
    status = com.process_incoming_frames()
    assert status == ProcessState.OK
    # Check message
    assert com.lastMessage == bytes([x for x in range(FRAME_PAYLOAD_SIZE)])


def test_comms_read_multiple_frames():
    # Call back on successful message
    def on_received_message(message: bytes):
        assert message == bytes([x for x in range(0, FRAME_PAYLOAD_SIZE*3)])

    com = Connection()
    com.set_received_message_callback(on_received_message)
    # Test data frame 1 of 3
    in_data = generate_frame(0, FRAME_PAYLOAD_SIZE)
    in_data.frameTotal = 3
    com.incoming_buffer = in_data.to_bytes()
    # Test read function
    status = com.process_incoming_frames()
    assert status == ProcessState.OK
    # Test data frame 2 of 3
    in_data = generate_frame(FRAME_PAYLOAD_SIZE, FRAME_PAYLOAD_SIZE*2)
    in_data.frameTotal = 3
    in_data.frameOrder = 2
    com.incoming_buffer = in_data.to_bytes()
    # Test read function
    status = com.process_incoming_frames()
    assert status == ProcessState.OK
    # Test data frame 3 of 3
    in_data = generate_frame(FRAME_PAYLOAD_SIZE*2, FRAME_PAYLOAD_SIZE*3)
    in_data.frameTotal = 3
    in_data.frameOrder = 3
    com.incoming_buffer = in_data.to_bytes()
    # Test read function
    status = com.process_incoming_frames()
    assert status == ProcessState.OK

    # Check message
    assert len(com.lastMessage) == FRAME_PAYLOAD_SIZE*3
    assert com.lastMessage == bytes([x for x in range(0, FRAME_PAYLOAD_SIZE*3)])


def test_comms_read_multiple_frames_out_of_order():
    # Call back on successful message
    def on_received_message(message: bytes):
        assert message == bytes([x for x in range(0, FRAME_PAYLOAD_SIZE*3)])

    com = Connection()
    com.set_received_message_callback(on_received_message)
    # Test data frame 2 of 3
    in_data = generate_frame(FRAME_PAYLOAD_SIZE, FRAME_PAYLOAD_SIZE*2)
    in_data.frameTotal = 3
    in_data.frameOrder = 2
    com.incoming_buffer = in_data.to_bytes()
    # Test read function
    status = com.process_incoming_frames()
    assert status == ProcessState.OK
    # Test data frame 1 of 3
    in_data = generate_frame(0, FRAME_PAYLOAD_SIZE)
    in_data.frameTotal = 3
    com.incoming_buffer = in_data.to_bytes()
    # Test read function
    status = com.process_incoming_frames()
    assert status == ProcessState.OK
    # Test data frame 3 of 3
    in_data = generate_frame(FRAME_PAYLOAD_SIZE*2, FRAME_PAYLOAD_SIZE*3)
    in_data.frameTotal = 3
    in_data.frameOrder = 3
    com.incoming_buffer = in_data.to_bytes()
    # Test read function
    status = com.process_incoming_frames()
    assert status == ProcessState.OK

    # Check message
    assert len(com.lastMessage) == FRAME_PAYLOAD_SIZE*3
    assert com.lastMessage == bytes([x for x in range(0, FRAME_PAYLOAD_SIZE*3)])


def test_comms_write():

    com = Connection()
    com.send_message(bytes([x for x in range(0, FRAME_PAYLOAD_SIZE*3)]))

    status = com.process_outgoing_frames()
    assert status == ProcessState.OK

    frame1 = Frame(com.outgoing_buffer[0:64])
    assert frame1.is_valid() is True
    frame2 = Frame(com.outgoing_buffer[64:128])
    assert frame2.is_valid() is True
    frame3 = Frame(com.outgoing_buffer[128:192])
    assert frame3.is_valid() is True


def test_comms_threading():
    # Call back on successful message
    def on_received_message(message: bytes):
        assert message == bytes([x for x in range(FRAME_PAYLOAD_SIZE)])

    com = Connection()
    com.set_received_message_callback(on_received_message)
    com.start()

    # Test data
    in_data = generate_frame()
    com.incoming_buffer = in_data.to_bytes()

    # Send data
    com.send_message(bytes([x for x in range(0, FRAME_PAYLOAD_SIZE)]))

    # Wait
    sleep(0.1)

    # Check frame
    print(len(com.outgoing_buffer))
    frame1 = Frame(com.outgoing_buffer[0:64])
    assert frame1.is_valid() is True

    # Stop thread
    com.stop()
