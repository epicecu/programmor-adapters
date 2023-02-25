import { defineStore } from 'pinia'
import SocketSerivce from '@/socket/socket'
import { compile } from 'vue'
import protobuf from 'protobufjs';

export enum AdapterStatus {
    Failed = -2,
    Unavailable = -1,
    Disconencted = 0,
    Connecting = 1,
    Connected = 2,
}

export enum DeviceStatus {
    Failed = -1,
    Disconencted = 0,
    Disconnecting = 1,
    Connecting = 2,
    Connected = 3,
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
    deviceId: string, // Adapter generated device id
    common1: any,
    connected: boolean,
    status: DeviceStatus
}

let Common1Message: protobuf.Type;
protobuf.load("src/proto/transaction.proto", (err, root) => {
    if(err){
        throw err;
    }
    if(!root){
        throw "Protobuf unavailable";
    }
    Common1Message = root.lookupType("Common1");
    // const test = Common1Message?.create();
    // console.log(test)
});

export const useHmiStore = defineStore('hmi', {
    state: () => ({ 
        adapters: [] as AdapterInfo[], 
        devices: [] as DeviceInfo[],
        connectedAdapter: -1 as number, // -1 Not connected, 0 and greater connected
        selectedDevice: "" as string, // "" Device not selected or available, else device selected
        unavailableCounter: 0 as number
    }),
    getters: {
        getAdapters: (state) => {
            // Returns all the adapters
            return state.adapters;
        },
        getAdapter: (state) => {
            return (adapterId: number) => state.adapters.find((adapter) => adapter.adapterId === adapterId)
        },
        getDevices: (state) => {
            // Returns all the devices for the given adapterId
            return (adapterId: number) => state.devices.filter((device) => device.adapterId === adapterId)
        },
        getDevice: (state) => {
            // Returns all the devices for the given adapterId
            return (deviceId: string) => state.devices.find((device) => device.deviceId === deviceId)
        },
    },
    actions: {
        // Adapter state functions
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
            const id = this.adapters.findIndex((adapter) => adapter.adapterId === updatedAdapter.adapterId);
            if(id < 0){
                return false;
            }
            this.adapters[id] = updatedAdapter;
            return true;
        },
        removeAdapter(adapterId: number): boolean{
            const id = this.adapters.findIndex((adapter) => adapter.adapterId === adapterId);
            if(id < 0){
                return false;
            }
            this.adapters.splice(id, 1);
            return true;
        },
        // Device state functions
        addDevice(device: DeviceInfo){
            const foundDevice = this.getDevice(device.deviceId);
            if(foundDevice){
                this.updateDevice(device);
            }else{
                this.devices.push(device);
            }
        },
        updateDevice(updatedDevice: DeviceInfo): boolean{
            const id = this.devices.findIndex((device) => device.deviceId === updatedDevice.deviceId);
            if(id < 0){
                return false;
            }
            this.devices[id] = updatedDevice;
            return true;
        },
        removeDevice(deviceId: string){
            const id = this.devices.findIndex((device) => device.deviceId === deviceId);
            if(id < 0){
                return false;
            }
            if(deviceId === this.selectedDevice){
                this.selectedDevice = "";
            }
            this.devices.splice(id, 1);
            return true;
        },
        removeAllDevicesForAdapter(adapterId: number){
            const devices = this.getDevices(adapterId);
            devices.forEach(device => {
                this.removeDevice(device.deviceId);
            });
        },
        // Action functions
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
                // Remove devices for this adapter
                this.removeAllDevicesForAdapter(adapterId);
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
                console.log("Connected to adapter "+adapter.adapterName + " sid: "+SocketSerivce.getSocket().id);
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
            // Handles the Device connection
            SocketSerivce.getSocket().on("connected", (deviceId) => {
                console.log("Adapter Connected to device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Connected;
                    this.updateDevice(device);
                }
            });
            SocketSerivce.getSocket().on("disconnected", (deviceId) => {
                console.log("Adapter Disconnected from device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Disconencted;
                    this.updateDevice(device);
                }
            });
            SocketSerivce.getSocket().on("connected_failed", (deviceId) => {
                console.log("Adapter Failed to connect to device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Failed;
                    this.updateDevice(device);
                }
            });
            SocketSerivce.getSocket().on("disconnected_failed", (deviceId) => {
                console.log("Adapter Failed to disconnect from device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Failed;
                    this.updateDevice(device);
                }
            });
            // Handle API
            SocketSerivce.getSocket().on("devices_detailed", (responseDevices) => {
                console.log("Handle devices_detailed", responseDevices);
                // Clear devices
                // this.devices = [] as DeviceInfo[];
                // Add devices to list
                responseDevices.forEach((responseDevice: any) => {
                    const message = Common1Message.fromObject(JSON.parse(responseDevice["common1"]))
                    let device = {} as DeviceInfo;
                    device.adapterId = this.connectedAdapter;
                    device.connected = false;
                    device.deviceId = responseDevice["deviceId"]
                    device.common1 = message.toJSON();
                    device.status = DeviceStatus.Disconencted;
                    this.addDevice(device);
                    console.log(device);
                });
            }),
            SocketSerivce.getSocket().on("message_data", (transactionData) => {
                console.log("On receive data: ", transactionData);
            });
        },
        // Emits
        requestDetailedDevices(){
            if(this.getAdapter(this.connectedAdapter)?.status === AdapterStatus.Connected){
                SocketSerivce.getSocket().emit("get_devices_detailed", "_");
            }
        },
        requestConnectDevice(deviceId: string){
            let device = this.getDevice(deviceId)
            if(device){
                device.status = DeviceStatus.Connecting;
                this.updateDevice(device);
            }
            SocketSerivce.getSocket().emit("connect_device", deviceId);
        },
        requestDisconnectDevice(deviceId: string){
            let device = this.getDevice(deviceId)
            if(device){
                device.status = DeviceStatus.Disconnecting;
                this.updateDevice(device);
            }
            SocketSerivce.getSocket().emit("disconnect_device", deviceId);
        },
        requestShare(deviceId: string, shareId: number){
            SocketSerivce.getSocket().emit("request_share", deviceId, shareId);
        },
        requestPublish(deviceId: string, shareId: number, data: JSON){

        },
        // Others
        updateSelectedDevice(deviceId: string){
            this.selectedDevice = deviceId;
            console.log("Updated selected device", deviceId);
        }
    },
})