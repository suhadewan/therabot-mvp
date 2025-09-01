"""
Database Configuration
Easy switching between SQLite and PostgreSQL
"""

# Database Configuration
DATABASE_CONFIG = {
    # Current database type
    "type": "sqlite",  # Options: "sqlite", "postgresql"
    
    # SQLite Configuration
    "sqlite": {
        "db_path": "mental_health_bot.db"
    },
    
    # PostgreSQL Configuration
    "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "mental_health_bot",
        "username": "your_username",
        "password": "your_password",
        # Connection string format: postgresql://username:password@host:port/database
        "connection_string": "postgresql://your_username:your_password@localhost:5432/mental_health_bot"
    }
}

def get_database_config():
    """Get current database configuration"""
    return DATABASE_CONFIG

def switch_to_sqlite(db_path: str = "mental_health_bot.db"):
    """Switch to SQLite database"""
    DATABASE_CONFIG["type"] = "sqlite"
    DATABASE_CONFIG["sqlite"]["db_path"] = db_path
    print(f"Switched to SQLite database: {db_path}")

def switch_to_postgresql(host: str = "localhost", port: int = 5432, 
                        database: str = "mental_health_bot", 
                        username: str = "your_username", 
                        password: str = "your_password"):
    """Switch to PostgreSQL database"""
    DATABASE_CONFIG["type"] = "postgresql"
    DATABASE_CONFIG["postgresql"].update({
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password,
        "connection_string": f"postgresql://{username}:{password}@{host}:{port}/{database}"
    })
    print(f"Switched to PostgreSQL database: {host}:{port}/{database}")

def get_current_db_type():
    """Get current database type"""
    return DATABASE_CONFIG["type"]

def get_connection_params():
    """Get connection parameters for current database type"""
    db_type = DATABASE_CONFIG["type"]
    if db_type == "sqlite":
        return {"db_path": DATABASE_CONFIG["sqlite"]["db_path"]}
    elif db_type == "postgresql":
        return {"connection_string": DATABASE_CONFIG["postgresql"]["connection_string"]}
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

# Example usage:
if __name__ == "__main__":
    print("Current database configuration:")
    print(f"Type: {get_current_db_type()}")
    print(f"Params: {get_connection_params()}")
    
    print("\nSwitching to PostgreSQL...")
    switch_to_postgresql(
        host="your-postgres-host",
        username="your_username",
        password="your_password",
        database="mental_health_bot"
    )
    
    print(f"New type: {get_current_db_type()}")
    print(f"New params: {get_connection_params()}") 