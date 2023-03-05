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
        messages: [] as MessageInfo[]
    }),
    getters: {
        getShare: (state) => {
            // Returns all the adapters
            return (shareId: number) => {
                const shares =  state.messages.filter((message) => message.shareId === shareId);
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
    },
    actions: {
        addMessage(message: MessageInfo){
            this.messages.push(message);
        }
    }
});