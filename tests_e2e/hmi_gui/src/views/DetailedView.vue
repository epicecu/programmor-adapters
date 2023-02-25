<script lang="ts">
import { DeviceStatus, useHmiStore } from '@/stores/hmi'
import { storeToRefs } from 'pinia';
import type { DeviceInfo } from '@/stores/hmi';

export default {
  setup(){
    // const socket
    const store = useHmiStore()
    const { selectedDevice } = storeToRefs(store)
    return {
        store,
        selectedDevice,
        DeviceStatus
    }
  },
  computed:{
    device(){
        return this.store.getDevice(this.selectedDevice);
    }
  },
  methods:{
    requestMessage(shareId: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.store.requestShare(this.device?.deviceId, shareId);
            console.log("Requested share "+shareId);
        }
    }
  }
};
</script>

<template>
    <div class="container">
    <main v-if="selectedDevice">
        <h1 class="display-4">Detailed View</h1>
        <h1 class="display-5">{{ device?.common1.deviceName }}</h1>
        
        <div v-if="device?.status === DeviceStatus.Connected">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th scope="col">Adapter Device Id</th>
                        <th scope="col">Protobuf Device Id</th>
                        <th scope="col">Registory Id</th>
                        <th scope="col">Shares Version</th>
                        <th scope="col">Serial Number</th>
                        <th scope="col">Firmware Version</th>
                    </tr>
                </thead>
                <tbody>
                <tr>
                    <th scope="row">{{ device?.deviceId }}</th>
                    <td>{{ device?.common1.id }}</td>
                    <td>{{ device?.common1.registryId }}</td>
                    <td>{{ device?.common1.sharesVersion }}</td>
                    <td>{{ device?.common1.serialNumber }}</td>
                    <td>{{ device?.common1.firmwareVersion }}</td>
                </tr>
                </tbody>
            </table>
        
            <button class="btn bg-white" @click="requestMessage(1)">Request Common1 Message</button>
        </div>
        <p v-if="device?.status === DeviceStatus.Connecting">Connecting</p>
        <p v-if="device?.status === DeviceStatus.Disconnecting">Disconnecting</p>
        <p v-if="device?.status === DeviceStatus.Failed">Failed</p>
    </main>
    </div>
</template>
