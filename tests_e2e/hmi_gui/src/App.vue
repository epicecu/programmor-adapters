<script setup lang="ts">
</script>

<template>
  <div class="app-inner container-fluid min-100 d-flex flex-column">
    <nav class="navbar navbar-expand bg-white flex-shrink-0 app-header">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">
          <img alt="Programmor Adapter HMI Test App"  src="@/assets/epicecu-programmor-logo.png" height="55">
        </a>

        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link to="/" class="nav-link">Dashboard</router-link>
            </li>
            <li class="nav-item">
              <a class="nav-link disabled" href="https://epicecu.com">EpicECU</a>
            </li>
            <li class="nav-item">
              <a class="nav-link disabled" href="https://programmor.com">Programmor</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <RouterView/>
  </div>
</template>

<style scoped>
  .app-inner{
    padding-left: 0;
    padding-right: 0;
  }
  
</style>
