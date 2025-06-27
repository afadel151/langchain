<script setup lang="ts">
import type { ChatOutput } from "@/shared/types";
import { IncompleteJsonParser } from "incomplete-json-parser";
import { InferenceClient } from "@huggingface/inference";
const client = new InferenceClient("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");
const parser = new IncompleteJsonParser();
const isGenerating = ref(false);
const text = ref("");
const textAreaRef = ref<HTMLTextAreaElement | null>(null);
function setOutputs(newValue: ChatOutput[] | ((prev: ChatOutput[]) => ChatOutput[])) {
  if (typeof newValue === "function") {
    outputs.value = newValue(outputs.value);
  } else {
    outputs.value = newValue;
  }
  emit("update-outputs", outputs.value);

}
const setIsGenerating = (state: boolean) => { };

const props = defineProps<{
  outputs: ChatOutput[]
}>()

const outputs = ref(props.outputs)
const emit = defineEmits(["update-outputs"]);
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

const sendMessage = async (message: string, conversation_id: string) => {
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
      body: JSON.stringify({ content: message, conversation_id: conversation_id })
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    // Check if response body exists
    if (!res.body) {
      throw new Error("No response body");
    }

    // Get the reader from the response body (not from res.json())
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    
    let done = false;
    let answer = { answer: "", tools_used: [] };
    let currentSteps: { name: string; result: Record<string, string> }[] = [];
    let buffer = "";
    let currentStepName = "";
    let currentStepContent = "";
    let insideStep = false;

    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      
      if (value) {
        let chunkValue = decoder.decode(value, { stream: true });
        console.log(`Received chunk: ${chunkValue}`);
        buffer += chunkValue;

        // Process buffer for complete tokens
        while (buffer.length > 0) {
          if (buffer.startsWith('<step><step_name>')) {
            // Start of a new step
            const stepNameEndIndex = buffer.indexOf('</step_name>');
            if (stepNameEndIndex !== -1) {
              const stepNameStart = buffer.indexOf('<step_name>') + '<step_name>'.length;
              currentStepName = buffer.substring(stepNameStart, stepNameEndIndex);
              console.log(`Starting step: ${currentStepName}`);
              
              // Remove the processed part from buffer
              buffer = buffer.substring(stepNameEndIndex + '</step_name>'.length);
              insideStep = true;
              currentStepContent = "";
            } else {
              // Wait for more data
              break;
            }
          } else if (buffer.startsWith('</step>') && insideStep) {
            // End of current step
            buffer = buffer.substring('</step>'.length);
            console.log(`Ending step: ${currentStepName}`);
            console.log(`Step content: ${currentStepContent}`);
            
            try {
              if (currentStepName === "final_answer") {
                // Parse final answer
                if (currentStepContent.trim()) {
                  const parsedAnswer = JSON.parse(currentStepContent.trim());
                  answer = parsedAnswer;
                  console.log(`Final answer parsed: ${JSON.stringify(answer)}`);
                }
              } else {
                // Parse tool step
                if (currentStepContent.trim()) {
                  const parsedResult = JSON.parse(currentStepContent.trim());
                  currentSteps.push({ 
                    name: currentStepName, 
                    result: parsedResult 
                  });
                  console.log(`Tool step added: ${currentStepName}`);
                }
              }
            } catch (parseError) {
              console.error(`Error parsing step content for ${currentStepName}:`, parseError);
              console.error(`Content was: ${currentStepContent}`);
            }

            // Reset step tracking
            insideStep = false;
            currentStepName = "";
            currentStepContent = "";
            
            // Remove </step> from buffer
            buffer = buffer.substring('</step>'.length);
          } else if (insideStep) {
            // We're inside a step, accumulate content
            const match = buffer.match(/({.*})/s); // greedy match for JSON object
            if (match) {
              currentStepContent = match[1]; // only store one JSON block
            }
            buffer = "";
          } else {
            // Look for the start of next step or consume one character
            const nextStepIndex = buffer.indexOf('<step>');
            if (nextStepIndex === -1) {
              // No more steps in buffer, consume all
              if (insideStep) {
                currentStepContent += buffer;
              }
              buffer = "";
            } else {
              // Found next step, consume up to that point
              if (insideStep) {
                currentStepContent += buffer.substring(0, nextStepIndex);
              }
              buffer = buffer.substring(nextStepIndex);
            }
          }
        }

        // Update output with current progress
        setOutputs((prevOutputs) => {
          const lastOutput = prevOutputs[prevOutputs.length - 1];
          return [
            ...prevOutputs.slice(0, -1),
            {
              ...lastOutput,
              steps: [...currentSteps],
              result: answer,
            },
          ];
        });
      }
    }

    console.log("Streaming completed");
    console.log(`Final steps: ${JSON.stringify(currentSteps)}`);
    console.log(`Final answer: ${JSON.stringify(answer)}`);

  } catch (error) {
    console.error("Error in sendMessage:", error);
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
    <div class="w-full relative flex z-0 items-center  bg-gray-300 rounded-lg border border-gray-100">
      <textarea v-model="text" ref="textAreaRef" @keydown.enter.prevent="submitOnEnter" @input="adjustHeight"
        class="w-full text-gray-800 z-0  p-3 bg-transparent min-h-24 focus:outline-none focus-visible:ring-0 focus-visible:ring-ring/50 resize-none"
        placeholder="Type your message here...">
      </textarea>
      <Button type="submit" :disabled="isGenerating || !text"
        class="  absolute right-5 w-fit p-5  rounded-full hover:translate-x-1 hover:bg-gray-500 z-10">
        <ArrowRight />
      </Button>
    </div>
  </form>
</template>
