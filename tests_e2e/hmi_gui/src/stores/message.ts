import { defineStore } from 'pinia'

// store.addMessage({"messageType": "share", "shareId": transactionData["shareId"], "message": messageWDefaults, "createdAt": Date.now()});

export enum MessageType {
    COMMON = 0,
    SHARE = 1
}

export interface MessageInfo {
    type: MessageType
    shareId: number,
    message: any,
    createdAt: number
}

export const useMessageStore = defineStore('message', {
    state: () => ({
        messages: [] as MessageInfo[],
        throughput: 0 as Number
    }),
    getters: {
        getShare: (state) => {
            // Returns all the adapters
            return (shareId: number) => {
                const shares =  state.messages.filter((message) => message.shareId === shareId  && message.type === MessageType.SHARE);
                let foundShare = shares[0];
                if(shares){
                    shares.forEach(share => {
                        if(share.createdAt > foundShare.createdAt){
                            foundShare = share;
                        }
                    });
                }
                return foundShare;
            }
        },
        clear: (state) => {
            return () => {
                state.messages = [];
            }
        }
    },
    actions: {
        addMessage(message: MessageInfo){
            if(this.messages.length>0){
                const last = this.messages[this.messages.length - 1]
                this.throughput = 1000/(message.createdAt - last.createdAt);
            }
            this.messages.push(message);
        },
    }
});