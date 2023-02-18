import { defineStore } from 'pinia'
import SocketSerivce from '@/socket/socket'

export enum AdapterStatus {
    Failed = -2,
    Unavailable = -1,
    Disconencted = 0,
    Connecting = 1,
    Connected = 2,
}

export interface AdapterInfo {
    adapterId: number
    adapterName: string,
    ipAddress: string,
    portNumber: number,
    connected: boolean,
    status: AdapterStatus,
    lastRequest: Date
}

export interface DeviceInfo {
    adapterId: number, // Links to the AdapterInfo
    registryId: number,
    serialNumber: number,
    sharesVersion: number,
    firmwareVersion: number,
    deviceName: string,
    connected: boolean,
}

export const useHmiStore = defineStore('hmi', {
    state: () => ({ 
        adapters: [] as AdapterInfo[], 
        devices: [] as DeviceInfo[],
        connectedAdapter: -1 as number, // -1 Not connected, 0 and greater connected
        unavailableCounter: 0 as number
    }),
    getters: {
        getAdapters: (state) => {
            // Returns all the adapters
            return state.adapters;
        },
        getAdapter: (state) => {
            return (adapterId: number) => state.adapters.find((adapter) => adapter.adapterId == adapterId)
        },
        getDevices: (state) => {
            // Returns all the devices for the given adapterId
            return (adapterId: number) => state.devices.filter((device) => device.adapterId == adapterId)
        },
    },
    actions: {
        addAdapter(adapter: AdapterInfo): number{
            if(adapter.adapterId === undefined || adapter.adapterId === null){
                const lastAdapter = this.adapters.at(-1);
                if(lastAdapter !== undefined){
                    adapter.adapterId = lastAdapter.adapterId + 1;
                }else{
                    adapter.adapterId = 0;
                }
            }
            this.adapters.push(adapter);
            return adapter.adapterId
        },
        updateAdapter(updatedAdapter: AdapterInfo): boolean{
            const id = this.adapters.findIndex((adapter) => adapter.adapterId == updatedAdapter.adapterId);
            if(id < 0) return false;
            this.adapters[id] = updatedAdapter;
            return true;
        },
        removeAdapter(adapterId: number): boolean{
            const id = this.adapters.findIndex((adapter) => adapter.adapterId == adapterId);
            if(id < 0) return false;
            this.adapters.slice(id, 1);
            return true;
        },
        connectAdapter(adapterId: number){
            console.log("Connecting to adatper "+adapterId);
            this.disconnectAll();
            let adapter = this.getAdapter(adapterId);
            if(adapter){
              SocketSerivce.connectSocket(adapter.ipAddress, adapter.portNumber);
              this.socketHandlers(adapter);
              adapter.connected = true;
              adapter.status = AdapterStatus.Connecting;
              this.connectedAdapter = adapter.adapterId;
              this.unavailableCounter = 0; // reset counter
              this.updateAdapter(adapter);
            }
        },
        disconnectAdapter(adapterId: number){
            console.log("Disconnecting from adatper "+adapterId);
            let adapter = this.getAdapter(adapterId);
            if(adapter){
                SocketSerivce.disconnectSocket();
                adapter.connected = false;
                adapter.status = AdapterStatus.Disconencted;
                this.connectedAdapter = -1;
                this.updateAdapter(adapter);
            }
        },
        disconnectAll(){
            this.adapters.forEach((adapter) =>{
                if(adapter.connected){
                    this.disconnectAdapter(adapter.adapterId);
                }
            })
        },
        socketHandlers(adapter: AdapterInfo){
            // Handles the Adapter connection
            SocketSerivce.getSocket().on("connect", () => {
                console.log("Connected to adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Connected;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket().on("disconnect", () => {
                console.log("Disconencted from adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Disconencted;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket().on("error", () => {
                console.log("An error occured with adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Failed;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket().on("close", () => {
                console.log("Lost connecteciton to adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Unavailable;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket().on("connect_error", () => {
                console.log("Failed to connect to adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Connecting;
                this.unavailableCounter++;
                this.updateAdapter(adapter);
                // Goto Error state
                if(this.unavailableCounter > 3){
                    adapter.status = AdapterStatus.Failed;
                    this.updateAdapter(adapter);
                }
            });
            // Handle API

        },
    },
})
