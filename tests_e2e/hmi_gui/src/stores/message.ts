import { defineStore } from 'pinia'

export const useMessageStore = defineStore('message', {
    state: () => ({
        messages: [] as any
    }),
    getters: {

    },
    actions: {
        addMessage(message: any){
            this.messages.push(message);
        }
    }
});