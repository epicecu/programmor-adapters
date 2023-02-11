import { io, Socket } from "socket.io-client";
import { useHmiStore } from '@/stores/hmi'
// import type { AdapterInfo } from "@/stores/hmi";

class SocketService {

    socket?: Socket;
    store = useHmiStore()

    constructor(){
        // Not used
    }

    addHandlers(){
        // On receive, Emit
    }

    connectAdapter(adapterId: number){
        let adapter = this.store.getAdapter(adapterId);
        if(adapter){
            this.connectSocket(adapter.ipAddress, adapter.portNumber);
            adapter.connected = true;
            this.store.updateAdapter(adapter);
        }
    }

    disconnectAdapter(adapterId: number){
        let adapter = this.store.getAdapter(adapterId);
        if(adapter){
            this.disconnectSocket();
            adapter.connected = false;
            this.store.updateAdapter(adapter);
        }
    }

    connectSocket(ipAddress: string, portNumber: number){
        const url = ipAddress+":"+portNumber;
        console.log("Connecting to adapter at "+url);
        this.socket = io(url);
    }

    disconnectSocket(){
        if(this.socket) {
            this.socket.disconnect();
        }
    }
}

export default new SocketService();