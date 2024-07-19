import { v4 as uuidv4 } from 'uuid';

interface Message {
    event: string,
    args: any[]
}

export class Socket {
    socket: WebSocket;
    id: string;
    events: Map<string, Function> = new Map();
    constructor(url: string) {
        this.socket = new WebSocket(url)
        this.id = uuidv4() as string;

        this.socket.addEventListener('open', (_) => {
            this.handleCallback('connect');
        });

        this.socket.addEventListener('close', (_) => {
            this.handleCallback('close');
            // this.handleCallback('disconnect');
        });

        this.socket.addEventListener('error', (_) => {
            this.handleCallback('error');
        });

        this.socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data) as Message;
            this.handleCallback(data.event, ...data.args);
        });
    }

    public disconnect(): void {
        this.socket.close();
    }

    public on(eventName: string, callbackFn: Function): void {
        this.events.set(
            eventName,
            callbackFn
        );
    }

    public emit(eventName: string, ...args): void {
        this.socket.send(JSON.stringify({'event': eventName, 'args': args} as Message));
    }

    private handleCallback(eventName: string, ...args: any[]): void {
        const fn = this.events.get(eventName);
        if(fn){
            fn(...args);
        }
    }
}

class SocketService {
    // A map of sockets to socketId
    sockets: Map<number, Socket> = new Map();

    connectSocket(socketId: number, ipAddress: string, portNumber: number): void {
        const url = 'ws://' + ipAddress + ':' + portNumber;
        console.log('Socket ' + socketId + ' Connecting to adapter at ' + url);
        this.sockets.set(
            socketId,
            new Socket(url)
        );
    }

    disconnectSocket(socketId: number): void {
        const socket = this.sockets.get(socketId);
        if (socket) {
            socket.disconnect();
        }
    }

    getSocket(socketId: number): Socket | undefined {
        const socket = this.sockets.get(socketId);
        if (!socket) {
            return undefined;
        }
        return socket;
    }
}

export default new SocketService();
