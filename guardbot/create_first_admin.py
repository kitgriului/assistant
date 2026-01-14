#!/usr/bin/env python3
"""
Create first admin user for GuardBot
Usage: python create_first_admin.py <telegram_id> [username]
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import config to initialize DB
from bot.config import DB_URL
from database.session import init_db, get_session
from database.models import User
from utils.roles import Role


async def create_admin(telegram_id: int, username: str = None):
    """Create first admin user"""
    print(f"Creating admin user with Telegram ID: {telegram_id}")
    
    # Initialize database
    await init_db(DB_URL)
    
    # Create session
    async with get_session() as db:
        # Check if user already exists
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"User {telegram_id} already exists!")
            existing.role = Role.ADMIN
            existing.is_active = True
            await db.commit()
            print(f"✓ Updated user {telegram_id} to ADMIN role")
        else:
            user = User(
                telegram_id=telegram_id,
                username=username or f"admin_{telegram_id}",
                role=Role.ADMIN,
                is_active=True,
                is_registered=True
            )
            db.add(user)
            await db.commit()
            print(f"✓ Created admin user: {username or f'admin_{telegram_id}'}")
        
        print("\nAdmin user created successfully!")
        print("You can now restart the bot and use /start command")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_first_admin.py <telegram_id> [username]")
        print("\nTo find your Telegram ID:")
        print("  1. Open Telegram")
        print("  2. Send /start to @userinfobot")
        print("  3. Copy your ID")
        sys.exit(1)
    
    try:
        telegram_id = int(sys.argv[1])
        username = sys.argv[2] if len(sys.argv) > 2 else None
        
        asyncio.run(create_admin(telegram_id, username))
    except ValueError:
        print("Error: telegram_id must be a number")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
