<script lang="ts">
import { useHmiStore } from '@/stores/hmi'
import { storeToRefs } from 'pinia';
import type { DeviceInfo } from '@/stores/hmi';

export default {
  setup(){
    // const socket
    const store = useHmiStore()
    const { adapters, connectedAdapter } = storeToRefs(store)
    return {
      store,
      adapters,
      connectedAdapter
    }
  },
  data(){
    return {
      selected: 0 as number,
      devices: this.getDevices()
    }
  },
  methods:{
    selectDevice(id: number){
      this.selected = id;
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
    connectAdapter(adapterId: number){
      console.log("Connecting to adatper "+adapterId);
      this.store.connectAdapter(adapterId);
    },
    disconnectAdapter(adapterId: number){
      console.log("Disconnecting from adatper "+adapterId);
      this.store.disconnectAdapter(adapterId);
    }
  },
};
</script>

<template>
  <div class="list-group list-group-flush border-bottom scrollarea">
    <div v-for="(device, i) in devices" :key="i">
      <a @click="selectDevice(i)" href="#" class="list-group-item list-group-item-action" v-bind:class="selected==i?'active':''" aria-current="true">
        <div class="d-flex w-100 justify-content-between">
          <h5 class="mb-1">{{device.deviceName}}</h5>
        </div>
        <p class="mb-1">{{device.firmware}}</p>
      </a>
    </div>
    <router-link to="/" class="list-group-item list-group-item-action" v-if="connectedAdapter > -1">
      <p class="mb-1">
        Update
      </p>
    </router-link>
  </div>
  <p class="mb-1" v-if="connectedAdapter < 0">
    Connect to an Adapter to view available devices
  </p>
</template>
