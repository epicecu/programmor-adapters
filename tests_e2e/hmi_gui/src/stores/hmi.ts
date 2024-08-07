import { defineStore, storeToRefs } from 'pinia'
import SocketSerivce from '@/socket/socket'
import { compile } from 'vue'
import protobuf from 'protobufjs';
import { useMessageStore, MessageType } from '@/stores/message';
import type { MessageInfo } from '@/stores/message';

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

export enum ActionType {
    NA = 0,
    COMMON_REQUEST = 1,
    COMMON_PUBLISH = 2,
    COMMON_RESPONSE = 3,
    SHARE_REQUEST = 4,
    SHARE_PUBLISH = 5,
    SHARE_RESPONSE = 6
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
let Share1Message: protobuf.Type;
protobuf.load("src/proto/transaction.proto", (err, root) => {
    if(err){
        throw err;
    }
    if(!root){
        throw "Protobuf unavailable";
    }
    Common1Message = root.lookupType("Common1");
});
protobuf.load("src/proto/test.proto", (err, root) => {
    if(err){
        throw err;
    }
    if(!root){
        throw "Protobuf unavailable";
    }
    Share1Message = root.lookupType("Share1");
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
              SocketSerivce.connectSocket(adapterId, adapter.ipAddress, adapter.portNumber);
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
                SocketSerivce.disconnectSocket(adapterId);
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
            SocketSerivce.getSocket(adapter.adapterId).on("connect", () => {
                console.log("Connected to adapter "+adapter.adapterName + " sid: "+SocketSerivce.getSocket(adapter.adapterId).id);
                adapter.status = AdapterStatus.Connected;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket(adapter.adapterId).on("disconnect", () => {
                console.log("Disconencted from adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Disconencted;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket(adapter.adapterId).on("error", () => {
                console.log("An error occured with adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Failed;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket(adapter.adapterId).on("close", () => {
                console.log("Lost connecteciton to adapter "+adapter.adapterName);
                adapter.status = AdapterStatus.Unavailable;
                this.updateAdapter(adapter);
            });
            SocketSerivce.getSocket(adapter.adapterId).on("connect_error", () => {
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
            SocketSerivce.getSocket(adapter.adapterId).on("connected", (deviceId) => {
                console.log("Adapter Connected to device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Connected;
                    this.updateDevice(device);
                }
            });
            SocketSerivce.getSocket(adapter.adapterId).on("disconnected", (deviceId) => {
                console.log("Adapter Disconnected from device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Disconencted;
                    this.updateDevice(device);
                }
            });
            SocketSerivce.getSocket(adapter.adapterId).on("connected_failed", (deviceId) => {
                console.log("Adapter Failed to connect to device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Failed;
                    this.updateDevice(device);
                }
            });
            SocketSerivce.getSocket(adapter.adapterId).on("disconnected_failed", (deviceId) => {
                console.log("Adapter Failed to disconnect from device "+deviceId);
                let device = this.getDevice(deviceId)
                if(device){
                    device.status = DeviceStatus.Failed;
                    this.updateDevice(device);
                }
            });
            // Handle API
            SocketSerivce.getSocket(adapter.adapterId).on("devices_detailed", (responseDevices) => {
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
                    if(responseDevice["connected"]){
                        device.status = DeviceStatus.Connected;
                    }else{
                        device.status = DeviceStatus.Disconencted;
                    }
                    this.addDevice(device);
                    console.log(device);
                });
            }),
            SocketSerivce.getSocket(adapter.adapterId).on("message_data", (transactionData) => {
                console.log("On receive data: ", transactionData);
                // Time to parse the data into a protobuf message
                if(transactionData["actionType"] === ActionType.COMMON_RESPONSE){
                    // Pase common message type
                    const base64: string = transactionData["data"]
                    const data = Uint8Array.from(window.atob(base64), (v) => v.charCodeAt(0));
                    const message = Common1Message.decode(data);
                    console.log("Parsed common message ", message);
                    const store = useMessageStore()
                    let messageInfo = {} as MessageInfo;
                    messageInfo.type = MessageType.COMMON;
                    messageInfo.shareId = transactionData["shareId"];
                    messageInfo.message = message;
                    messageInfo.createdAt = Date.now();
                    store.addMessage(messageInfo);

                }else if(transactionData["actionType"] === ActionType.SHARE_RESPONSE){
                    // Pase share message type
                    const base64: string = transactionData["data"]
                    const data = Uint8Array.from(window.atob(base64), (v) => v.charCodeAt(0));
                    const message = Share1Message.decode(data);
                    const messageWDefaults = Share1Message.toObject(message, {
                        defaults: true
                    })
                    console.log("Parsed share message ", messageWDefaults);
                    const store = useMessageStore()
                    let messageInfo = {} as MessageInfo;
                    messageInfo.type = MessageType.SHARE;
                    messageInfo.shareId = transactionData["shareId"];
                    messageInfo.message = messageWDefaults;
                    messageInfo.createdAt = Date.now();
                    store.addMessage(messageInfo);
                }
            });
        },
        // Emits
        requestDetailedDevices(){
            if(this.getAdapter(this.connectedAdapter)?.status === AdapterStatus.Connected){
                SocketSerivce.getSocket(this.connectAdapter).emit("get_devices_detailed", "_");
            }
        },
        requestConnectDevice(deviceId: string){
            let device = this.getDevice(deviceId)
            if(device){
                device.status = DeviceStatus.Connecting;
                this.updateDevice(device);
            }
            SocketSerivce.getSocket(this.connectedAdapter).emit("connect_device", deviceId);
        },
        requestDisconnectDevice(deviceId: string){
            let device = this.getDevice(deviceId)
            if(device){
                device.status = DeviceStatus.Disconnecting;
                this.updateDevice(device);
            }
            SocketSerivce.getSocket(this.connectedAdapter).emit("disconnect_device", deviceId);
        },
        requestCommon(deviceId: string, shareId: number){
            SocketSerivce.getSocket(this.connectedAdapter).emit("request_common", deviceId, shareId);
        },
        requestShare(deviceId: string, shareId: number){
            SocketSerivce.getSocket(this.connectedAdapter).emit("request_share", deviceId, shareId);
        },
        requestPublish(deviceId: string, shareId: number, data: JSON){

        },
        setCommonSchedule(deviceId: string, shareId: number, interval: number){
            SocketSerivce.getSocket(this.connectedAdapter).emit("set_scheduled_common", deviceId, shareId, interval);
        },
        clearCommonSchedule(deviceId: string, shareId: number){
            SocketSerivce.getSocket(this.connectedAdapter).emit("clear_scheduled_common", deviceId, shareId);
        },
        setShareSchedule(deviceId: string, shareId: number, interval: number){
            SocketSerivce.getSocket(this.connectedAdapter).emit("set_scheduled_share", deviceId, shareId, interval);
        },
        clearShareSchedule(deviceId: string, shareId: number){
            SocketSerivce.getSocket(this.connectedAdapter).emit("clear_scheduled_share", deviceId, shareId);
        },
        publishShare(deviceId: string, shareId: number, counterStart: number, counterEnd: number){
            const payload = {
                startingNumber: counterStart,
                endingNumber: counterEnd,
                counter: 0
            }
            const message = Share1Message.create(payload);
            const data = Share1Message.encode(message).finish();
            var decoder = new TextDecoder('utf8');
            const base64 = window.btoa(decoder.decode(data));
            SocketSerivce.getSocket(1).emit("publish_share", deviceId, shareId, base64);
        },
        // Others
        updateSelectedDevice(deviceId: string){
            this.selectedDevice = deviceId;
            console.log("Updated selected device", deviceId);
        }
    },
})