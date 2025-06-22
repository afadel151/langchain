<script setup>
import 'highlight.js/styles/monokai.css';
const text = `# Hello World! **she**`
</script>


<template>
    <MarkdownRenderer :source="text" />
</template>