import asyncio
import aiohttp
import json

async def test_streaming_endpoint():
    """Test the streaming endpoint directly"""
    url = "http://127.0.0.1:8000/invoke"
    payload = {
        "content": "What is the weather like?",
        "conversation_id": "test_123"
    }
    print(f"Testing endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                if response.status != 200:
                    text = await response.text()
                    print(f"Error response: {text}")
                    return
                chunk_count = 0
                async for chunk in response.content.iter_chunked(1024):
                    chunk_count += 1
                    chunk_text = chunk.decode('utf-8')
                    print(f"\n--- Chunk #{chunk_count} ---")
                    print(f"Raw chunk: {repr(chunk_text)}")
                    print(f"Decoded: {chunk_text}")
                
                print(f"\nTotal chunks received: {chunk_count}")
    except Exception as e:
        print(f"Error testing endpoint: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_endpoint())