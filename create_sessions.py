import os
from telethon import TelegramClient
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class SessionCreator:
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.sessions_dir = 'sessions'
        
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)

    async def create_session(self, session_name):
        session_path = os.path.join(self.sessions_dir, f"{session_name}.session")
        client = TelegramClient(session_path, self.api_id, self.api_hash)
        
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"\nPlease login for session {session_name}")
                await client.start()
                print(f"Session {session_name} created successfully!")
            else:
                print(f"Session {session_name} already exists and is authorized.")
        except Exception as e:
            print(f"Error creating session {session_name}: {str(e)}")
        finally:
            await client.disconnect()

async def main():
    creator = SessionCreator()
    while True:
        session_name = input("\nEnter session name (or 'exit' to quit): ")
        if session_name.lower() == 'exit':
            break
        await creator.create_session(session_name)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())