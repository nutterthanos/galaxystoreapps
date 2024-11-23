import aiohttp
import asyncio
import aiofiles
from aiohttp import ClientSession

# Function to generate product IDs
def generate_product_ids(start=0, end=1000, length=12):
    return [str(i).zfill(length) for i in range(start, end + 1)]

# Asynchronous function to send GET request
async def fetch(session: ClientSession, product_id: str):
    url = f"https://galaxystore.samsung.com/api/prepost/{product_id}?langCd=en"
    headers = {
        "Accept": "application/xhtml+xml;charset=UTF-8"
    }
    try:
        async with session.get(url, headers=headers) as response:
            content = await response.read()
            if response.status == 200:
                # Check for error codes or messages in the response content
                if b"<errCode>E4002</errCode>" in content or b"<errMsg>Application NotFound</errMsg>" in content:
                    print(f"Skipping product ID: {product_id} due to error in content.")
                    return product_id, None
                return product_id, content
            else:
                print(f"Failed to retrieve data for product ID: {product_id} with status code {response.status}")
                return product_id, None
    except Exception as e:
        print(f"Error fetching product ID: {product_id}: {e}")
        return product_id, None

# Asynchronous function to save the response content using aiofiles
async def save_response(product_id: str, content: bytes):
    if content:
        filename = f"{product_id}.xhtml"
        async with aiofiles.open(filename, "wb") as file:
            await file.write(content)
        print(f"Saved response for product ID: {product_id}")

# Main asynchronous function with task limiting
async def main():
    product_ids = generate_product_ids(7762553, 7900000)
    task_limit = 500  # Limit the number of concurrent tasks

    async with aiohttp.ClientSession() as session:
        tasks = []
        for product_id in product_ids:
            # Start the fetch task and add it to the list of tasks
            task = asyncio.create_task(fetch(session, product_id))
            tasks.append(task)

            # If the number of tasks reaches the limit, wait for them to complete
            if len(tasks) >= task_limit:
                responses = await asyncio.gather(*tasks)
                save_tasks = [save_response(pid, content) for pid, content in responses if content]
                await asyncio.gather(*save_tasks)
                tasks = []  # Reset the tasks list

        # Handle any remaining tasks after the loop completes
        if tasks:
            responses = await asyncio.gather(*tasks)
            save_tasks = [save_response(pid, content) for pid, content in responses if content]
            await asyncio.gather(*save_tasks)

if __name__ == "__main__":
    asyncio.run(main())