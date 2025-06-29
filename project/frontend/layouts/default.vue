<template>
  <SidebarProvider>
    <AppSidebar />
    <main class="w-full h-screen ">
      <SidebarTrigger />
      <div class="flex flex-col justify-center items-center px-40 h-full">
        <slot />
      </div>
    </main>
  </SidebarProvider>
</template>
