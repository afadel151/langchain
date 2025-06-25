<template>
  <SidebarProvider>
    <AppSidebar />
    <main class="w-full h-screen overflow-y-hidden">
      <SidebarTrigger />
      <div class="flex flex-col justify-center items-center px-10 h-full">
        <slot />
      </div>
    </main>
  </SidebarProvider>
</template>
