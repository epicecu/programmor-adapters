import { defineStore } from 'pinia'

export interface AdapterInfo {
    adapterId: number
    adapterName: string,
    ipAddress: string,
    portNumber: number,
    connected: boolean,
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
        devices: [] as DeviceInfo[]
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
            return (adapterId: number) => state.devices.find((device) => device.adapterId == adapterId)
        },
    },
    actions: {
        addAdapter(adapter: AdapterInfo): number{
            if(adapter.adapterId === undefined || adapter.adapterId == null){
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
        }
    },
})
