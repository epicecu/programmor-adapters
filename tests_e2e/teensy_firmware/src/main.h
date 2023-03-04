#include <Arduino.h>
#include <usb.h>

#include <pb_decode.h>
#include <pb_encode.h>
#include "transaction.pb.h"
#include "test.pb.h"


corelib::USB usb;

void setup();

void loop();

/**
 * @brief Processes the incoming message and produces an outgoing message
 * 
 * @param buffer Incoming/Outgoing proto message data
 * @return HandleMessageState 
 */
corelib::HandleMessageState usingProto(corelib::Buffer* buffer);