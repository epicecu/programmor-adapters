<script lang="ts">
// import { ref } from 'vue'

export default {
  data(){
    return {
      adapters: [{
        adapterName: "Usb Hid",
        address: "localhost",
        port: 4000
      },
      {
        adapterName: "Canbus",
        address: "localhost",
        port: 4100
      },
      {
        adapterName: "Ethernet",
        address: "localhost",
        port: 4100
      }],
      selected: 0
    }
  },
  methods:{
    selectAdapter(id: number){
      this.selected = id;
    }
  }
};

</script>

<template>
  <div class="list-group list-group-flush border-bottom scrollarea">
    <div v-for="(adapter, i) in adapters" :key="i">
      <a @click="selectAdapter(i)" href="#" class="list-group-item list-group-item-action" v-bind:class="selected==i?'active':''" aria-current="true">
        <div class="d-flex w-100 justify-content-between">
          <h5 class="mb-1">{{adapter.adapterName}}</h5>
        </div>
        <p class="mb-1">{{adapter.address}}:{{adapter.port}}</p>
      </a>
    </div>
  </div>
</template>
