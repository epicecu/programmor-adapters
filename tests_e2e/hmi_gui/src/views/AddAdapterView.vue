<script lang="ts">
import { useHmiStore } from '@/stores/hmi'
import type { AdapterInfo } from '@/stores/hmi'
import { storeToRefs } from 'pinia'
import ActionbarComponent from '@/views/ActionBarComponent.vue'
import router from '@/router';

export default {
  setup(){
    const store = useHmiStore()
    return {
      store
    }
  },
  data(){
    return {
      name: "" as string,
      ipAddress: "localhost" as string,
      portNumber: 5000 as number,
      errors: [] as string[]
    }
  },
  methods:{
    addAdapter(){
      console.log("Add adapter button clicked");
      if(this.name === "" ){
        return this.errors.push("Please enter a valid Adapter Name");
      }
      if(this.ipAddress === ""){
        return this.errors.push("Please enter a valid Ip Address");
      }
      if(this.portNumber === null){
        return this.errors.push("Please enter a valid Port Number")
      }
      console.log("Creating Adapter");
      let newAdapter = {} as AdapterInfo;
      newAdapter.adapterName = this.name;
      newAdapter.ipAddress = this.ipAddress;
      newAdapter.portNumber = this.portNumber;
      newAdapter.connected = false;
      const adapterId = this.store.addAdapter(newAdapter);
      if(adapterId > 0){
        console.log("Okay");
        return router.push("/")
      }
      console.log("Faiiled to add new adapter");
    },
    closeWarning(index: number){
      // TODO: Need to make this more reliable
      this.errors.pop();
    }
  },
  components:{
    ActionbarComponent
  }
};

</script>

<template>
  <actionbar-component>
    <li class="nav-item">
      <router-link to="/" class="nav-link text-light">Return</router-link>
    </li>
  </actionbar-component>

  <div class="container">
    <h1>Add an Adapter</h1>
    <form @submit.prevent>
      <div class="mb-3">
        <label for="adapterNameInput" class="form-label">Name</label>
        <input type="text" class="form-control" id="adapterNameInput" v-model="name" required>
      </div>
      <div class="mb-3">
        <label for="adapterIpAddress" class="form-label">Ip Address</label>
        <input type="text" class="form-control" id="adapterIpAddress" v-model="ipAddress" required>
      </div>
      <div class="mb-3">
        <label for="adapterPortNumber" class="form-label">Port Number</label>
        <input type="number" class="form-control" id="adapterPortNumber" v-model="portNumber" required>
      </div>
      <div v-for="(error, index) in errors">
        <div class="alert alert-warning" role="alert">
          {{ error }}
          <button @click="closeWarning(index)" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      </div>
      <button @click="addAdapter" class="btn btn-primary">Create</button>
    </form>
  </div>
</template>
