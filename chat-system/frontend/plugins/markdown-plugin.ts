import Markdown from 'vue3-markdown-it'

export default defineNuxtPlugin((nuxtApp) => {
    // e.g. register a plugin or global component
    nuxtApp.vueApp.use(Markdown)
  })