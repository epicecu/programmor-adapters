import { io, Socket } from "socket.io-client";

class SocketService {

    socket: Socket;

    constructor(){
        this.socket = io("localhost:4000", { // Set default in hmi.json
            autoConnect: false
        })
    }

    addHandlers(){
        // On receive, Emit
    }

    connectSocket(ipAddress: string, portNumber: number){
        const url = ipAddress+":"+portNumber+"/api";
        console.log("Connecting to adapter at "+url);
        this.socket = io(url, {
            reconnectionAttempts: 5
        });
    }

    disconnectSocket(){
        if(this.socket) {
            this.socket.disconnect();
        }
    }

    getSocket(){
        return this.socket;
    }
}

export default new SocketService();