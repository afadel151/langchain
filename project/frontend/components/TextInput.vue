<script setup lang="ts">
import type { ChatOutput } from "@/shared/types";
import { IncompleteJsonParser } from "incomplete-json-parser";
import { InferenceClient } from "@huggingface/inference";
const client = new InferenceClient("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");
const parser = new IncompleteJsonParser();
const isGenerating = ref(false);
const text = ref("");
const textAreaRef = ref<HTMLTextAreaElement | null>(null);
function setOutputs(
  newValue: ChatOutput[] | ((prev: ChatOutput[]) => ChatOutput[])
) {
  if (typeof newValue === "function") {
    outputs.value = newValue(outputs.value);
  } else {
    outputs.value = newValue;
  }
}
const setIsGenerating = (state: boolean) => { };

const outputs = ref<ChatOutput[]>([]);

async function submit(e: any) {
  e.preventDefault();
  if (outputs.value.length == 0) {
    let generated_title : string | undefined = ""
    try {
      
      const chatCompletion = await client.chatCompletion({
        provider: "auto",
        model: "microsoft/Phi-3-mini-4k-instruct",
        messages: [
          {
            role: "user",
            content: `Generate a maximum 5 words conversation title from the following text: "${text.value}"`,
          },
        ],
      });
      generated_title = chatCompletion.choices[0].message.content
      console.log("Generated title:", generated_title);
    } catch (error) {
      console.log("Error creating conversation:", error);
    }
    try {
      const res = await fetch("http://127.0.0.1:8000/create_conversation", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title: generated_title || "New Conversation" }),
      });
      const data = await res.json();  // ⬅️ THIS reads the body!
      sendMessage(text.value,data.conversation_id);
      text.value = "";
    } catch (error) {
      console.log("Error creating conversation:", error);
    }
  }
  
}

const sendMessage = async (message: string,conversation_id: string) => {
  const newOutputs = [
    ...outputs.value,
    {
      question: text.value,
      steps: [],
      result: {
        answer: "",
        tools_used: [],
      },
    },
  ];
  setOutputs(newOutputs);
  setIsGenerating(true);
  try {
    const res = await fetch(`http://127.0.0.1:8000/invoke`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content: message, conversation_id : conversation_id })
    });

    if (!res.ok) {
      throw new Error("Error");
    }

    const data = await res.json();  
    console.log(data);
    
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
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      let chunkValue = decoder.decode(value);
      console.log(`chunk : ${chunkValue}`);
      buffer += chunkValue;
      if (buffer.includes("</step_name>")) {
        const stepNameMatch = buffer.match(/<step_name>([^<]*)<\/step_name>/);
        if (stepNameMatch) {
          const [_, stepName] = stepNameMatch;
          try {
            if (stepName !== "final_answer") {
              const fullStepPattern =
                /<step><step_name>([^<]*)<\/step_name>([^<]*?)(?=<step>|<\/step>|$)/g;
              const matches = [...buffer.matchAll(fullStepPattern)];
              for (const match of matches) {
                const [fullMatch, matchStepName, jsonStr] = match;
                if (jsonStr) {
                  try {
                    const result = JSON.parse(jsonStr);
                    currentSteps.push({ name: matchStepName, result });
                    buffer = buffer.replace(fullMatch, "");
                  } catch (error) { }
                }
              }
            } else {
              // If it's the final answer step, parse the streaming JSON using incomplete-json-parser
              const jsonMatch = buffer.match(
                /(?<=<step><step_name>final_answer<\/step_name>)(.*)/
              );
              if (jsonMatch) {
                const [_, jsonStr] = jsonMatch;
                parser.write(jsonStr);
                const result = parser.getObjects();
                answer = result;
                parser.reset();
              }
            }
          } catch (error) {
            console.error("Error parsing step name:", error);
          }
        }
      }
      // Update output with current content and steps
      setOutputs((prevOuputs) => {
        const lastOutput = prevOuputs[prevOuputs.length - 1];
        return [
          ...prevOuputs.slice(0, -1),
          {
            ...lastOutput,
            steps: currentSteps,
            result: answer,
          },
        ];
      });
    }
  } catch (error) {
    console.error("Error:", error);
    setIsGenerating(false);
  } finally {
    setIsGenerating(false);
  }
};

function submitOnEnter(event: any) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submit(event);
  }
}
const adjustHeight = () => {
  nextTick(() => {
    const textArea = textAreaRef.value;
    if (textArea) {
      textArea.style.height = "auto";
      textArea.style.height = `${textArea.scrollHeight}px`;
    }
  });
};

watch(text, (newValue) => {
  if (textAreaRef.value) {
    adjustHeight();
  }
});
function handleResize() {
  adjustHeight();
}

// When component is mounted
onMounted(() => {
  window.addEventListener("resize", handleResize);
  adjustHeight(); // Optionally call once on mount
});

// Clean up when component is destroyed
onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
});
import { ArrowRight } from "lucide-vue-next";
</script>

<template>
  <form @submit.prevent="submit" class="flex gap-3 z-0" :class="outputs.length > 0
    ? 'fixed bottom-0 left-0 right-0 bg-white p-4 shadow-lg'
    : ''
    ">
    <div class="w-full relative flex z-0 items-center  bg-gray-800 rounded-lg border border-gray-600">
      <textarea v-model="text" ref="textAreaRef" @keydown.enter.prevent="submitOnEnter" @input="adjustHeight"
        class="w-full text-white z-0  p-3 bg-transparent min-h-24 focus:outline-none focus-visible:ring-0 focus-visible:ring-ring/50 resize-none"
        placeholder="Type your message here...">
      </textarea>
      <Button type="submit" :disabled="isGenerating || !text"
        class="  absolute right-5 w-fit p-5  rounded-full hover:translate-x-1 hover:bg-gray-500 z-10">
        <ArrowRight />
      </Button>
    </div>
  </form>
</template>
