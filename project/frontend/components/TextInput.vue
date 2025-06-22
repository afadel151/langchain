<script setup lang="ts">
import type { ChatOutput }  from '@/shared/types'
import { IncompleteJsonParser } from 'incomplete-json-parser';

const parser = new IncompleteJsonParser();
const isGenerating = ref(false)
const text = ref('')
const textArea = ref<HTMLTextAreaElement | null>(null)
const setOutPuts = (newOutputs : any) => {
  
}
const setIsGenerating = (state: boolean) => {
}   

const outputs = ref<ChatOutput[]>([])

async function subimt(e: Event){
    e.preventDefault()

    text.value = ""
}

const sendMessage = async (message: string) => {
    const newOutputs = [...outputs.value,{
        question : text.value,
        steps: [],
        result: {
            answer: '',
            tools_used: [],
        }
    }]
    setOutPuts(newOutputs)
    setIsGenerating(true);
    try {
      const res = await fetch(`http://localhost:8000/invoke?content=${text}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(text),
      });

      if (!res.ok) {
        throw new Error("Error");
      }

      const data = res.body;
      if (!data) {
        setIsGenerating(false);
        return;
      }

      const reader = data.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let answer = { answer: "", tools_used: [] };
      let currentSteps: { name: string; result: Record<string, string> }[] = [];
      let buffer = "";
      while (!done) {
        
      }
    }
    catch (error) {
      console.error("Error:", error);
      setIsGenerating(false);
    }
    finally {
      setIsGenerating(false);
    }
}
</script>

<template>

</template>