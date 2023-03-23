<script lang="ts">
import { DeviceStatus, useHmiStore } from '@/stores/hmi'
import { useMessageStore } from '@/stores/message';
import { storeToRefs } from 'pinia';
import type { DeviceInfo } from '@/stores/hmi';
import type { MessageInfo } from '@/stores/message';

export default {
  setup(){
    // const socket
    const storeHmi = useHmiStore()
    const { selectedDevice } = storeToRefs(storeHmi)
    const storeMessage = useMessageStore()
    const { messages, throughput } = storeToRefs(storeMessage)
    return {
        storeHmi,
        selectedDevice,
        DeviceStatus,
        storeMessage,
        messages,
        throughput
    }
  },
  data(){
    return {
        counterStart: 0 as number,
        counterEnd: 50 as number
    }
  },
  computed:{
    device(){
        return this.storeHmi.getDevice(this.selectedDevice);
    },
    share1(){
        return this.storeMessage.getShare(1);
    },
  },
  watch:{
    share1: function(share: MessageInfo){
        if(share){
            this.counterStart = share.message["startingNumber"];
            this.counterEnd = share.message["endingNumber"];
        }
    }
  },
  methods:{
    requestCommon(shareId: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.requestCommon(this.device?.deviceId, shareId);
            console.log("Requested Common "+shareId);
        }
    },
    requestShare(shareId: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.requestShare(this.device?.deviceId, shareId);
            console.log("Requested Share "+shareId);
        }
    },
    setCommonSchedule(shareId: number, interval: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.setCommonSchedule(this.device?.deviceId, shareId, interval);
            console.log("Set Schedule Common "+shareId+" Interval "+interval);
        }
    },
    clearCommonSchedule(shareId: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.clearCommonSchedule(this.device?.deviceId, shareId);
            console.log("Clear Schedule Common "+shareId);
        }
    },
    setShareSchedule(shareId: number, interval: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.setShareSchedule(this.device?.deviceId, shareId, interval);
            console.log("Set Schedule Share "+shareId+" Interval "+interval);
        }
    },
    clearShareSchedule(shareId: number){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.clearShareSchedule(this.device?.deviceId, shareId);
            console.log("Clear Schedule Share "+shareId);
        }
    },
    publishCounterParams(){
        if(this.device){
            if(this.device.status === DeviceStatus.Disconencted || this.device.status === DeviceStatus.Failed){
                return console.warn("Not connected to device "+this.device.deviceId);
            }
            this.storeHmi.publishShare(this.device?.deviceId, 1, this.counterStart, this.counterEnd);
        }
        console.log("Pub")
    },
    clear(){
        this.storeMessage.clear();
    }
  }
};
</script>

<template>
    <div class="detailed-view overflow-auto">
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

            <div class="mt-4">
                <div class="">
                    <p class="m-1">Common1 Schedule</p>
                    <button class="btn bg-white m-1" @click="requestCommon(1)">Request Message</button>
                    <button class="btn bg-white m-1" @click="setCommonSchedule(1, 2000)">Set Commmon1 Schedule 2s</button>
                    <button class="btn bg-white m-1" @click="clearCommonSchedule(1)">Clear Commmon1 Schedule 2s</button>
                </div>
                <div>
                    <p class="m-1">Share1 Schedule</p>
                    <button class="btn bg-white m-1" @click="requestShare(1)">Request Message</button>
                    <button class="btn bg-white m-1" @click="setShareSchedule(1, 1000)">Set 1Hz</button>
                    <button class="btn bg-white m-1" @click="setShareSchedule(1, 400)">Set 2.5Hz</button>
                    <button class="btn bg-white m-1" @click="setShareSchedule(1, 200)">Set 5Hz</button>
                    <button class="btn bg-white m-1" @click="setShareSchedule(1, 100)">Set 10Hz</button>
                    <button class="btn bg-white m-1" @click="setShareSchedule(1, 66.66)">Set 15Hz</button>
                    <button class="btn bg-white m-1" @click="setShareSchedule(1, 33.33)">Set 30Hz</button>
                    <button class="btn bg-white m-1" @click="setShareSchedule(1, 22)">Set 41Hz</button>
                    <button class="btn bg-dark text-white m-1" @click="setShareSchedule(1, 16.66)">Set 60Hz</button>
                    <button class="btn bg-dark text-white m-1" @click="setShareSchedule(1, 10)">Set 100Hz</button>
                    <button class="btn bg-white m-1" @click="clearShareSchedule(1)">Clear</button>
                </div>
            </div>

            <div class="mt-4">
                <div class="row">
                    <p>Publish Share1 to the device<br>Inputs value's will automatically update when a Share1 message is received</p>
                    <p>Counter: {{ share1?.message["counter"] }}</p>
                    <div class="col-3">
                        <div class="mb-3">
                            <label for="counterStartingValue" class="form-label">Counter Starting Value</label>
                            <input type="number" class="form-control" id="counterStartingValue" placeholder="0" v-model="counterStart">
                        </div>
                    </div>
                    <div class="col-3">
                        <div class="mb-3">
                            <label for="counterStartingValue" class="form-label">Counter Ending Value</label>
                            <input type="number" class="form-control" id="counterStartingValue" placeholder="0" v-model="counterEnd">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-2">
                        <button class="btn bg-white" @click="publishCounterParams">Publish</button>
                    </div>
                </div>
            </div>

            <div class="mt-4">
                <p>Total messages: {{ messages.length }} Throughput: {{ throughput }}Hz</p> <button class="btn bg-white m-1" @click="clear">Clear</button>

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
    </div>
</template>

<style scoped>
  .detailed-view{
    max-height: calc(100vh - 56px - 81px); 
  }
  .h-0{
    height: 0;
  }
  .footer{
    height: 200px;
  }
  
</style>
