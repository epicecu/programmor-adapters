# Programmor Adapters End-to-End Tests

Performs a full end to end test of the Programmor adapter using a test HMI Gui application and test Teensy firmware for the comms loopback.

## Perform e2e Test

1. Connect a Teensy 3.x or 4.x development board
2. Build and Upload the `teensy_firmware` to the Teensy (Windows: Run as Administrator)
3. Start the `Programmor-Adapter` application
4. Start the `hmi_gui` application
5. Open the hmi application at `http://localhost:5173`

## Hmi

![Hmi Screenshot v1.0.0 Wip](../support/hmi-wip-v1.0.png)
