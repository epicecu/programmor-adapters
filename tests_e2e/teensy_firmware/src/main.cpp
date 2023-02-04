#include "main.h"

// corelib::USB usb();

void setup()
{
    // Init the usb comms
    usb.initilise();
    // Register callback function
    auto fn = [](corelib::Buffer* b){
        return usingProto(b);
    };
    usb.setHandleMessageCallback(fn);
}

void loop()
{
    usb.iterate();
}

corelib::HandleMessageState usingProto(corelib::Buffer* buffer)
{
    // Checks if the buffer is within the acceptable range to decode
    if(buffer->inIndex == 0){
        return corelib::HandleMessageState::NO_DATA;
    }

    // In Stream & object
    TransactionMessage inMessage = TransactionMessage_init_zero;
    pb_istream_t inStream = pb_istream_from_buffer(buffer->inBuffer, TransactionMessage_size);

    // Decode the message
    if(!pb_decode(&inStream, TransactionMessage_fields, &inMessage)){
        buffer->inIndex = 0;
        return corelib::HandleMessageState::FAILED_DECODE;
    }

    /**
     * Handle the Share requests & Common requests
     */
    if(inMessage.action == TransactionMessage_Action_COMMON){
        // Response
        TransactionMessage outMessage = TransactionMessage_init_zero;
        pb_ostream_t outStream = pb_ostream_from_buffer(buffer->outBuffer, sizeof(buffer->outBuffer));

        outMessage.token = inMessage.token;
        outMessage.action = TransactionMessage_Action_RESPONSE;

        // Common message request
        if(inMessage.action == TransactionMessage_Action_COMMON){
        if(inMessage.shareId == 1){
            Common1 common1 = Common1_init_zero;
            common1.id = 2;
            strcpy(common1.deviceName, "programmor-firmware-test");
            common1.registryId = 1;
            common1.sharesVersion = 1;
            common1.firmwareVersion = 202301;
            common1.serialNumber = 123456789;
            // copy common1 into the response message
            pb_ostream_t common1Stream = pb_ostream_from_buffer(outMessage.data, Common1_size);
            pb_encode(&common1Stream, Common1_fields, &common1);
            outMessage.shareId = 1;
            outMessage.dataLength = common1Stream.bytes_written;
        }
        }

    }

    // Reset in buffer length
    buffer->inIndex = 0;

    return corelib::HandleMessageState::OK;
    }