import usb.core
import usb.util
import libusb_package

from shared.frame import Frame

# The dev can be searched for using the vender and product ids, we simply need to store this as a tuple for device lookups.

for dev in libusb_package.find(find_all=True):
    if dev is None:
        continue

    try:
        assert dev.manufacturer is not None
        assert dev.product is not None
    except Exception as e:
        continue

    print(f"{dev.manufacturer} {dev.product}")

    # if dev.manufacturer != "Teensyduino":
    #     continue

    # dev.set_configuration()

    configuration = dev.get_active_configuration()

    print("---break")
    for i, interface in enumerate(configuration):
        if dev.is_kernel_driver_active(i):
            dev.detach_kernel_driver(i)
            # We may want to reattach the device back to the kernel,,, not sure if required

        endpoint_out = usb.util.find_descriptor(
            interface,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        endpoint_in = usb.util.find_descriptor(
            interface,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

        if endpoint_out is None or endpoint_in is None:
            continue

        request_frame = Frame()
        request_frame.preamble = 0x02
        request_frame.checksum()
        request_frame_as_bytes = bytes(request_frame.to_bytes())
        print(request_frame)
        try:
            endpoint_out.write(request_frame_as_bytes)
        except usb.core.USBTimeoutError:
            continue
        print("-----next operation")
        try:
            received = endpoint_in.read(64, 1)
        except usb.core.USBTimeoutError:
            continue
        received_as_bytes = bytes(received)
        received_frame = Frame()
        received_frame.from_bytes(received_as_bytes)
        print(received_frame)
        print("-----next interface")

    print("----------------------------")

