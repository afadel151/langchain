<script setup lang="ts">
import type { Conversation } from "@/shared/types";
import { InferenceClient } from "@huggingface/inference";

const isGenerating = ref(false);
const text = ref("");
import { GoogleGenerativeAI } from "@google/generative-ai";
const configuration = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY || "AIzaSyAinZK6Y8l_giTTToEyBJjh3tAsHnfwvUc");
const model = configuration.getGenerativeModel({ model: "gemini-2.0-flash" });
const textAreaRef = ref<HTMLTextAreaElement | null>(null);

const setIsGenerating = (state: boolean) => { };
const conversation_id = ref<string>("");
const props = defineProps<{
  conversation: Conversation | null
}>()

const messages = ref(props.conversation?.messages)
const emit = defineEmits(["update-outputs"]);
async function submit(e: any) {
  e.preventDefault();
  console.log("Submitting message:", text.value);

  if (messages.value?.length == 0) {
    let generated_title: string | undefined = ""
    try {
      console.log('Generating title ....');

      const result = await model.generateContent(`Return one conversation title (maximum of 4 words) from the following text: "${text.value}" . don't use markdown return in txt format`);
      const response = result.response;

      generated_title = response.text();
      console.log('Generated Title : ', generated_title);
      try {
        const res = await fetch("http://127.0.0.1:8000/create_conversation", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ title: generated_title || "New Conversation" }),
        });
        const data = await res.json();  // ⬅️ THIS reads the body
        conversation_id.value = data.conversation_id;
        sendMessage(text.value, data.conversation_id);
        text.value = "";
      } catch (error) {
        console.log("Error creating conversation:", error);
      }
    } catch (error) {
      console.log("Error creating conversation:", error);
    }

  } else {
    sendMessage(text.value, conversation_id.value);
  }

}

const sendMessage = async (message: string, conversation_id: string) => {
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
            insideStep = false;
            currentStepName = "";
            currentStepContent = "";
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
      }
    }

    console.log("Streaming completed");
    console.log(`Final steps: ${JSON.stringify(currentSteps)}`);
    console.log(`Final answer: ${JSON.stringify(answer)}`);
    emit("update-outputs", {
      "question": text.value,
      "response": {
        "answer": answer.answer,
        "tools_used": answer.tools_used,
        "steps": currentSteps
      }
    })
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
  <form @submit.prevent="submit" class="flex gap-3 z-0" :class="(messages ?? []).length > 0
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
