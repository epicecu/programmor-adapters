<script lang="ts">
import { useHmiStore } from '@/stores/hmi'
import { storeToRefs } from 'pinia'
import ActionbarComponent from '@/views/ActionBarComponent.vue'

export default {
  setup(){
    const store = useHmiStore()
    return {
    }
  },
  data(){
    return {
    }
  },
  methods:{
  },
  mounted(){
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
  <h1>Add an Adapter</h1>
</template>
