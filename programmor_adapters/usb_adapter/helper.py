from typing import Tuple
import usb.core


def get_device_endpoints(dev: usb.core.Device) -> Tuple[usb.core.Endpoint, usb.core.Endpoint]:
    """Get Device Endpoints

    return: Tuple[endpoint_in, endpoint_out] or None
    """
    configuration = dev.get_active_configuration()
    # Iterate through interfaces for device
    for i, interface in enumerate(configuration):
        # Fix for linux operating systems
        try:
            if dev.is_kernel_driver_active(i):
                dev.detach_kernel_driver(i)
                # We may want to reattach the device back to the kernel,,, not sure if required
        except NotImplementedError:
            pass
        # Find the available in endpoint (HID)
        endpoint_in: usb.core.Endpoint = usb.util.find_descriptor(
            interface,
            # match the first OUT endpoint
            custom_match=lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_IN)
        # Find the available out endpoint (HID)
        endpoint_out: usb.core.Endpoint = usb.util.find_descriptor(
            interface,
            # match the first OUT endpoint
            custom_match=lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_OUT)
        if endpoint_in is None or endpoint_out is None:
            return None, None
        return endpoint_in, endpoint_out
    return None, None
