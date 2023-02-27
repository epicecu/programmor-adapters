<script lang="ts">
import { DeviceStatus, useHmiStore } from '@/stores/hmi'
import { useMessageStore } from '@/stores/message';
import { storeToRefs } from 'pinia';
import type { DeviceInfo } from '@/stores/hmi';

export default {
  setup(){
    // const socket
    const storeHmi = useHmiStore()
    const { selectedDevice } = storeToRefs(storeHmi)
    const storeMessage = useMessageStore()
    const { messages } = storeToRefs(storeMessage)
    return {
        storeHmi,
        selectedDevice,
        DeviceStatus,
        storeMessage,
        messages
    }
  },
  computed:{
    device(){
        return this.storeHmi.getDevice(this.selectedDevice);
    }
  },
  methods:{
    requestMessage(shareId: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.requestShare(this.device?.deviceId, shareId);
            console.log("Requested share "+shareId);
        }
    }
  }
};
</script>

<template>
    <div class="container">
    <main v-if="selectedDevice">
        <h1 class="display-3">{{ device?.common1.deviceName }}</h1>
        <p class="lead">Detailed View</p>
        
        <div v-if="device?.status === DeviceStatus.Connected">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th scope="col">Props</th>
                        <th scope="col">Data</th>
                    </tr>
                </thead>
                <tbody>
                <tr>
                    <td>Adapter Device Id</td>
                    <td>{{ device?.deviceId }}</td>
                </tr>
                <tr>
                    <td>Protobuf Device Id</td>
                    <td>{{ device?.common1.id }}</td>
                </tr>
                <tr>
                    <td>Registory Id</td>
                    <td>{{ device?.common1.registryId }}</td>
                </tr>
                <tr>
                    <td>Shares Version</td>
                    <td>{{ device?.common1.sharesVersion }}</td>
                </tr>
                <tr>
                    <td>Serial Number</td>
                    <td>{{ device?.common1.serialNumber }}</td>
                </tr>
                <tr>
                    <td>Firmware Version</td>
                    <td>{{ device?.common1.firmwareVersion }}</td>
                </tr>
                </tbody>
            </table>
        
            <button class="btn bg-white" @click="requestMessage(1)">Request Common1 Message</button>

            <div class="mt-3">
                <p>Total messages {{ messages.length }}</p>
    
                <div v-for="(message, i) in messages" :key="i">
                   ShareId {{ message["shareId"] }}, Message: {{ message["message"] }}
                </div>
            </div>
        </div>
        <p v-if="device?.status === DeviceStatus.Connecting">Connecting</p>
        <p v-if="device?.status === DeviceStatus.Disconnecting">Disconnecting</p>
        <p v-if="device?.status === DeviceStatus.Failed">Failed</p>
    </main>
    </div>
</template>
