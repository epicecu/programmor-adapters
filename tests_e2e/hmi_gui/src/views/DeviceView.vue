<script lang="ts">
import { DeviceStatus, useHmiStore } from '@/stores/hmi'
import { storeToRefs } from 'pinia';
import type { DeviceInfo } from '@/stores/hmi';

export default {
  setup(){
    // const socket
    const store = useHmiStore()
    const { adapters, devices, connectedAdapter, selectedDevice } = storeToRefs(store)
    return {
      store,
      adapters,
      devices,
      connectedAdapter,
      selectedDevice,
      DeviceStatus
    }
  },
  data(){
    return {
      selected: 0 as number,
      _devices: this.getDevices()
    }
  },
  methods:{
    selectDevice(device: DeviceInfo, id: number){
      this.selected = id;
      this.store.updateSelectedDevice(device.deviceId);
    },
    getDevices(){
      const devices = [] as DeviceInfo[];
      if(this.connectedAdapter > -1){
        const availableDevices = this.store.getDevices(this.connectedAdapter);
        availableDevices.forEach((device)=> {
          devices.push(device)
        })
      }
      return devices;
    },
    connectDevice(deviceId: string){
      console.log("Connecting to device");
      this.store.requestConnectDevice(deviceId);
    },
    disconnectDevice(deviceId: string){
      console.log("Disconnecting from device");
      this.store.requestDisconnectDevice(deviceId);
    },
    requestDetailedDevices(){
      this.store.requestDetailedDevices();
    }
  },
};
</script>

<template>
  <div class="list-group list-group-flush border-bottom scrollarea">
    <div v-for="(device, i) in devices" :key="i">
      <a @click="selectDevice(device, i)" href="#" class="list-group-item list-group-item-action" v-bind:class="selected==i?'active':''" aria-current="true">
        <div class="d-flex w-100 justify-content-between">
          <h5 class="mb-1">{{device.common1.deviceName}}</h5>
          <small v-if="device.status === DeviceStatus.Connected">Connected</small>
          <small v-if="device.status === DeviceStatus.Connecting">Connecting</small>
          <small v-if="device.status === DeviceStatus.Disconencted">Disconnected</small>
          <small v-if="device.status === DeviceStatus.Disconnecting">Disconnecting</small>
          <small v-if="device.status === DeviceStatus.Failed">Failed</small>
        </div>
        <p class="mb-1">Adapter device Id: {{ device.deviceId }}</p>
        <button v-if="device.status === DeviceStatus.Disconencted || device.status === DeviceStatus.Failed" class="btn bg-white" @click="connectDevice(device.deviceId)">Connect</button>
        <button v-if="device.status === DeviceStatus.Connected" class="btn bg-white" @click="disconnectDevice(device.deviceId)">Disconnect</button>
      </a>
    </div>
    <div to="/" class="list-group-item list-group-item-action" v-if="connectedAdapter > -1" @click="requestDetailedDevices">
      <p class="mb-1">
        Update
      </p>
    </div>
  </div>
  <p class="mb-1" v-if="connectedAdapter < 0">
    Connect to an Adapter to view available devices
  </p>
</template>
