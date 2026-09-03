import asyncio
import asyncpg

async def main():
    # Connect to the default postgres database to create a new one
    conn = await asyncpg.connect('postgresql://postgres:Dharshan%4009@localhost:5432/postgres')
    
    # Drop the test database if it exists
    try:
        await conn.execute('DROP DATABASE sif_sentinel_test (FORCE)')
    except asyncpg.exceptions.InvalidCatalogNameError:
        pass
    except Exception as e:
        print(f"Drop error: {e}")

    # Create the test database
    try:
        await conn.execute('CREATE DATABASE sif_sentinel_test')
        print("Test database 'sif_sentinel_test' created successfully.")
    except Exception as e:
        print(f"Create error: {e}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
