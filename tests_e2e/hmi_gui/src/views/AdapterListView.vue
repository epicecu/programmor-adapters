<script lang="ts">
import { useHmiStore } from '@/stores/hmi'
import { storeToRefs } from 'pinia';
import SocketSerivce from '@/socket/socket'

export default {
  setup(){
    // const socket
    const store = useHmiStore()
    const { adapters } = storeToRefs(store)
    return {
      store,
      adapters,
    }
  },
  data(){
    return {
      selected: 0 as number,
    }
  },
  methods:{
    selectAdapter(id: number){
      this.selected = id;
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
    <div v-for="(adapter) in adapters">
      <a @click="selectAdapter(adapter.adapterId)" href="#" class="list-group-item list-group-item-action" v-bind:class="selected==adapter.adapterId?'active':''" aria-current="true">
        <div class="d-flex w-100 justify-content-between">
          <h5 class="mb-1">{{adapter.adapterName}}</h5>
          <small v-if="!adapter.connected">Disconnected</small>
          <small v-if="adapter.connected">Connected</small>
        </div>
        <p class="mb-1">{{adapter.ipAddress}}:{{adapter.portNumber}}</p>
        <button v-if="!adapter.connected" class="btn bg-white" @click="connectAdapter(adapter.adapterId)">Connect</button>
        <button v-if="adapter.connected" class="btn bg-white" @click="disconnectAdapter(adapter.adapterId)">Disconnect</button>
      </a>
    </div>
    <router-link to="/adapter/add" class="list-group-item list-group-item-action">
      <p class="mb-1">
        Add Adapter
      </p>
    </router-link>
  </div>
</template>
