#include "main.h"

// corelib::USB usb();

void setup()
{
    // Counter defaults
    counterStart = 0;
    counterEnd = 100;
    counter = counterStart;
    elapsedTime = 0;

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
    // Process counter
    unsigned long currentTime = millis();
    // Each second
    if(currentTime - elapsedTime > 1000){
        counter++;
        // Counter has reached the end
        if(counter > counterEnd){
            // Reset counter
            counter = counterStart;
        }
        elapsedTime = currentTime;
    }

    // Process usb
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
    if(inMessage.action == TransactionMessage_Action_COMMON_REQUEST){
        // Response
        TransactionMessage outMessage = TransactionMessage_init_zero;
        pb_ostream_t outStream = pb_ostream_from_buffer(buffer->outBuffer, sizeof(buffer->outBuffer));

        outMessage.token = inMessage.token;
        outMessage.action = TransactionMessage_Action_COMMON_RESPONSE;

        // Common message request
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
        
        if(!pb_encode(&outStream, TransactionMessage_fields, &outMessage)){
            // Failed to encode
            return corelib::HandleMessageState::FAILED_ENCODE;
        }
        buffer->outMessageLength = outStream.bytes_written;

    }else if(inMessage.action == TransactionMessage_Action_SHARE_REQUEST){
        // Response
        TransactionMessage outMessage = TransactionMessage_init_zero;
        pb_ostream_t outStream = pb_ostream_from_buffer(buffer->outBuffer, sizeof(buffer->outBuffer));

        outMessage.token = inMessage.token;
        outMessage.action = TransactionMessage_Action_SHARE_RESPONSE;

        // Common message request
        if(inMessage.shareId == 1){
            Share1 share1 = Share1_init_zero;
            share1.startingNumber = counterStart;
            share1.endingNumber = counterEnd;
            share1.counter = counter;

            // copy share1 into the response message
            pb_ostream_t share1Stream = pb_ostream_from_buffer(outMessage.data, Share1_size);
            pb_encode(&share1Stream, Share1_fields, &share1);
            outMessage.shareId = 1;
            outMessage.dataLength = share1Stream.bytes_written;
        }
        
        if(!pb_encode(&outStream, TransactionMessage_fields, &outMessage)){
            // Failed to encode
            return corelib::HandleMessageState::FAILED_ENCODE;
        }
        buffer->outMessageLength = outStream.bytes_written;

    }else if(inMessage.action == TransactionMessage_Action_COMMON_PUBLISH){
        // Do nothing

    }else if(inMessage.action == TransactionMessage_Action_SHARE_PUBLISH){
        // Common message request
        if(inMessage.shareId == 1){
            Share1 share1 = Share1_init_zero;
            pb_istream_t share1Stream = pb_istream_from_buffer(inMessage.data, inMessage.dataLength);
            if(!pb_decode(&share1Stream, Share1_fields, &share1)){
                buffer->inIndex = 0;
                return corelib::HandleMessageState::FAILED_DECODE;
            }
            // Update counter params
            counterEnd = share1.endingNumber;
            counterStart = share1.startingNumber;
        }
    }

    // Reset in buffer length
    buffer->inIndex = 0;

    return corelib::HandleMessageState::OK;
}