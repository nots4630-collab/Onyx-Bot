import aiosqlite
import asyncio
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Initialize database connection and create tables"""
        async with self.lock:
            self.db = await aiosqlite.connect(self.db_path)
            await self.create_tables()
    
    async def create_tables(self):
        """Create all necessary database tables"""
        # Servers configuration
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                server_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '~',
                welcome_channel INTEGER,
                goodbye_channel INTEGER,
                log_channel INTEGER,
                autorole INTEGER,
                muted_role INTEGER,
                join_message INTEGER,
                leave_message INTEGER
            )
        ''')
        
        # Users data
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                discriminator TEXT,
                balance INTEGER DEFAULT 100,
                bank INTEGER DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                warnings INTEGER DEFAULT 0,
                kicks INTEGER DEFAULT 0,
                bans INTEGER DEFAULT 0,
                daily_claim TEXT,
                profile_color TEXT DEFAULT '#000000'
            )
        ''')
        
        # Economy transactions
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Warnings
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                warning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                server_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Level roles
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS level_roles (
                server_id INTEGER,
                level INTEGER,
                role_id INTEGER,
                PRIMARY KEY (server_id, level)
            )
        ''')
        
        await self.db.commit()
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
    
    # Server methods
    async def get_server(self, server_id):
        cursor = await self.db.execute('SELECT * FROM servers WHERE server_id = ?', (server_id,))
        return await cursor.fetchone()
    
    async def set_server(self, server_id, **kwargs):
        existing = await self.get_server(server_id)
        if existing:
            set_clause = ', '.join([f'{k} = ?' for k in kwargs])
            values = list(kwargs.values()) + [server_id]
            await self.db.execute(f'UPDATE servers SET {set_clause} WHERE server_id = ?', values)
        else:
            columns = 'server_id, ' + ', '.join(kwargs.keys())
            placeholders = '?, ' + ', '.join(['?' for _ in kwargs])
            values = [server_id] + list(kwargs.values())
            await self.db.execute(f'INSERT INTO servers ({columns}) VALUES ({placeholders})', values)
        await self.db.commit()
    
    # User methods
    async def get_user(self, user_id, username=None, discriminator=None):
        cursor = await self.db.execute(
            'SELECT * FROM users WHERE user_id = ?',
            (user_id,)
        )
        user = await cursor.fetchone()
        if not user and username:
            await self.db.execute(
                'INSERT INTO users (user_id, username, discriminator) VALUES (?, ?, ?)',
                (user_id, username, discriminator)
            )
            await self.db.commit()
            return await self.get_user(user_id)
        return user
    
    async def update_user_balance(self, user_id, amount, transaction_type, description):
        user = await self.get_user(user_id)
        if user:
            new_balance = user[3] + amount
            await self.db.execute(
                'UPDATE users SET balance = ? WHERE user_id = ?',
                (new_balance, user_id)
            )
            await self.db.execute(
                'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (user_id, amount, transaction_type, description)
            )
            await self.db.commit()
            return new_balance
        return None
    
    async def add_xp(self, user_id, amount):
        user = await self.get_user(user_id)
        if user:
            new_xp = user[6] + amount
            new_total_xp = user[5] + amount
            required_xp = user[7] * 100 * user[7]
            level_up = False
            new_level = user[7]
            
            while new_xp >= required_xp and new_level < 100:
                new_xp -= required_xp
                new_level += 1
                level_up = True
                required_xp = new_level * 100 * new_level
            
            await self.db.execute(
                'UPDATE users SET total_xp = ?, xp = ?, level = ? WHERE user_id = ?',
                (new_total_xp, new_xp, new_level, user_id)
            )
            await self.db.commit()
            return level_up, new_level, new_xp
        return False, 1, 0
    
    # Warning methods
    async def add_warning(self, user_id, moderator_id, reason, server_id):
        await self.db.execute(
            'INSERT INTO warnings (user_id, moderator_id, reason, server_id) VALUES (?, ?, ?, ?)',
            (user_id, moderator_id, reason, server_id)
        )
        await self.db.execute(
            'UPDATE users SET warnings = warnings + 1 WHERE user_id = ?',
            (user_id,)
        )
        await self.db.commit()
    
    async def get_warnings(self, user_id, server_id=None):
        if server_id:
            cursor = await self.db.execute(
                'SELECT * FROM warnings WHERE user_id = ? AND server_id = ? ORDER BY timestamp DESC',
                (user_id, server_id)
            )
        else:
            cursor = await self.db.execute(
                'SELECT * FROM warnings WHERE user_id = ? ORDER BY timestamp DESC',
                (user_id,)
            )
        return await cursor.fetchall()

# Global database instance
db = Database()