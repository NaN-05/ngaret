import asyncio
import random
import ssl
import json
import time
import uuid
import websockets
from loguru import logger
from fake_useragent import UserAgent

async def connect_to_wss(user_id):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid4())
    logger.info(f"Device ID: {device_id}")
    
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy2.wynd.network"
            
            # Connect to WebSocket server
            async with websockets.connect(uri, ssl=ssl_context, extra_headers=custom_headers, 
                                          server_hostname=server_hostname) as websocket:
                
                # Send ping every 5 seconds
                async def send_ping():
                    while True:
                        send_message = json.dumps({
                            "id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}
                        })
                        logger.debug(f"Sending PING: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(5)
                
                # Start ping task
                await asyncio.sleep(1)
                asyncio.create_task(send_ping())
                
                # Listen for responses
                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received message: {message}")
                    
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "desktop",
                                "version": "4.28.2",
                            }
                        }
                        logger.debug(f"Sending AUTH response: {auth_response}")
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(f"Sending PONG response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))

        except Exception as e:
            logger.error(f"Error with user ID {user_id}: {e}")

async def main():
    # Load user IDs from 'userid_list.txt' file
    try:
        with open('userid_list.txt', 'r') as file:
            user_ids = file.read().splitlines()

        # Create a task for each user ID
        tasks = [asyncio.ensure_future(connect_to_wss(user_id)) for user_id in user_ids]
        await asyncio.gather(*tasks)

    except FileNotFoundError:
        logger.error("File 'userid_list.txt' not found. Please create it and add user IDs.")
    except Exception as e:
        logger.error(f"Error loading user IDs: {e}")

if __name__ == '__main__':
    asyncio.run(main())