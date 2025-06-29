<template>
  <SidebarProvider>
    <AppSidebar />
    <main class="w-full h-screen flex flex-col overflow-y-hidden">
      <SidebarTrigger />
      <div class="flex flex-col justify-center items-center px-4 md:px-10 lg:px-20 xl:px-[18%] h-full">
        <slot />
      </div>
    </main>
  </SidebarProvider>
</template>
