<script lang="ts">
import { ref, onMounted } from 'vue'

// reactive state
const count = ref(0)

const data = [
  {
    deviceName: "Dev1",
    firmware: "aaaa"
  },{
    deviceName: "Dev2",
    firmware: "c99"
  }
]

// functions that mutate state and trigger updates
function increment() {
  count.value++
}

// lifecycle hooks
onMounted(() => {
  console.log(`The initial count is ${count.value}.`)
})

export default {
  data(){
    return {
      devices: [{
          deviceName: "Dev1",
          firmware: "aaaa"
        },
        {
          deviceName: "Dev2",
          firmware: "c99"
        }
      ],
      selected: 0
    }
  },
  methods:{
    selectDevice(id: number){
      this.selected = id;
    }
  }
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
  </div>
</template>
