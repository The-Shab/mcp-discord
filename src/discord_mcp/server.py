import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Any, List
from functools import wraps
import discord
from discord.ext import commands
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

def _configure_windows_encoding():
    if sys.platform == "win32":
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

_configure_windows_encoding()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")

# Discord bot setup
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Initialize Discord bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize MCP server
app = Server("discord-server")

# Store Discord client reference
discord_client = None

@bot.event
async def on_ready():
    global discord_client
    discord_client = bot
    logger.info(f"Logged in as {bot.user.name}")

# Helper function to ensure Discord client is ready
def require_discord_client(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not discord_client:
            raise RuntimeError("Discord client not ready")
        return await func(*args, **kwargs)
    return wrapper

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available Discord tools."""
    return [
        # Server Information Tools
        Tool(
            name="get_server_info",
            description="Get information about a Discord server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID"
                    }
                },
                "required": ["server_id"]
            }
        ),
        Tool(
            name="get_channels",
            description="Get a list of all channels in a Discord server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID"
                    }
                },
                "required": ["server_id"]
            }
        ),
        Tool(
            name="list_members",
            description="Get a list of members in a server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of members to fetch",
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["server_id"]
            }
        ),

        # Role Management Tools
        Tool(
            name="add_role",
            description="Add a role to a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User to add role to"
                    },
                    "role_id": {
                        "type": "string",
                        "description": "Role ID to add"
                    }
                },
                "required": ["server_id", "user_id", "role_id"]
            }
        ),
        Tool(
            name="remove_role",
            description="Remove a role from a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User to remove role from"
                    },
                    "role_id": {
                        "type": "string",
                        "description": "Role ID to remove"
                    }
                },
                "required": ["server_id", "user_id", "role_id"]
            }
        ),

        # Channel Management Tools
        Tool(
            name="create_text_channel",
            description="Create a new text channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "Channel name"
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Optional category ID to place channel in"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Optional channel topic"
                    }
                },
                "required": ["server_id", "name"]
            }
        ),
        Tool(
            name="delete_channel",
            description="Delete a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "ID of channel to delete"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for deletion"
                    }
                },
                "required": ["channel_id"]
            }
        ),

        # Message Reaction Tools
        Tool(
            name="add_reaction",
            description="Add a reaction to a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to react to"
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji to react with (Unicode or custom emoji ID)"
                    }
                },
                "required": ["channel_id", "message_id", "emoji"]
            }
        ),
        Tool(
            name="add_multiple_reactions",
            description="Add multiple reactions to a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to react to"
                    },
                    "emojis": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Emoji to react with (Unicode or custom emoji ID)"
                        },
                        "description": "List of emojis to add as reactions"
                    }
                },
                "required": ["channel_id", "message_id", "emojis"]
            }
        ),
        Tool(
            name="remove_reaction",
            description="Remove a reaction from a message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Message to remove reaction from"
                    },
                    "emoji": {
                        "type": "string",
                        "description": "Emoji to remove (Unicode or custom emoji ID)"
                    }
                },
                "required": ["channel_id", "message_id", "emoji"]
            }
        ),
        Tool(
            name="send_message",
            description="Send a message to a specific channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID"
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content"
                    }
                },
                "required": ["channel_id", "content"]
            }
        ),
        Tool(
            name="edit_message",
            description="Edit an existing message sent by the bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "ID of the message to edit"
                    },
                    "content": {
                        "type": "string",
                        "description": "New message content"
                    }
                },
                "required": ["channel_id", "message_id", "content"]
            }
        ),
        Tool(
            name="read_messages",
            description="Read recent messages from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of messages to fetch (max 100)",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["channel_id"]
            }
        ),
        Tool(
            name="get_user_info",
            description="Get information about a Discord user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Discord user ID"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="moderate_message",
            description="Delete a message and optionally timeout the user",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID containing the message"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "ID of message to moderate"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for moderation"
                    },
                    "timeout_minutes": {
                        "type": "number",
                        "description": "Optional timeout duration in minutes",
                        "minimum": 0,
                        "maximum": 40320  # Max 4 weeks
                    }
                },
                "required": ["channel_id", "message_id", "reason"]
            }
        ),
        Tool(
            name="list_servers",
            description="Get a list of all Discord servers the bot has access to with their details such as name, id, member count, and creation date.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        # Forum Channel Tools
        Tool(
            name="get_forum_posts",
            description="List all posts (threads) in a forum channel, including active and archived ones",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Forum channel ID"
                    }
                },
                "required": ["channel_id"]
            }
        ),
        Tool(
            name="read_forum_post",
            description="Read messages from a forum post (thread)",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "Thread/post ID to read messages from"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of messages to fetch (max 100)",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["thread_id"]
            }
        ),
        Tool(
            name="create_forum_post",
            description="Create a new post in a forum channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Forum channel ID"
                    },
                    "title": {
                        "type": "string",
                        "description": "Post title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Post content (first message)"
                    },
                    "tag_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of tag names to apply"
                    }
                },
                "required": ["channel_id", "title", "content"]
            }
        ),
        Tool(
            name="get_forum_tags",
            description="List available tags for a forum channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Forum channel ID"
                    }
                },
                "required": ["channel_id"]
            }
        ),
        # Server Structure Tools
        Tool(
            name="create_category",
            description="Create a new category channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "Category name"
                    }
                },
                "required": ["server_id", "name"]
            }
        ),
        Tool(
            name="create_forum_channel",
            description="Create a new forum channel in a server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "Forum channel name"
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Optional category ID to place forum in"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Optional forum topic/guidelines"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of tag names to create"
                    }
                },
                "required": ["server_id", "name"]
            }
        ),
        Tool(
            name="move_channel",
            description="Move a channel to a different category",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID to move"
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Target category ID (omit to remove from category)"
                    }
                },
                "required": ["channel_id"]
            }
        ),

        Tool(
            name="send_file",
            description="Send a file to a specific channel with an optional message",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Discord channel ID"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to upload"
                    },
                    "content": {
                        "type": "string",
                        "description": "Optional message content to send with the file"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional custom filename for the uploaded file"
                    }
                },
                "required": ["channel_id", "file_path"]
            }
        ),

        Tool(
            name="add_tags_to_post",
            description="Add tags to an existing forum post",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "Thread/post ID to add tags to"
                    },
                    "tag_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tag names to add"
                    }
                },
                "required": ["thread_id", "tag_names"]
            }
        ),

        # Permission Management Tools
        Tool(
            name="get_roles",
            description="List all roles in a Discord server with their IDs and permissions",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server (guild) ID"
                    }
                },
                "required": ["server_id"]
            }
        ),
        Tool(
            name="create_role",
            description="Create a new role in a server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "Role name"
                    },
                    "color": {
                        "type": "string",
                        "description": "Hex color code (e.g. '#ff0000')"
                    },
                    "hoist": {
                        "type": "boolean",
                        "description": "Whether to display role members separately"
                    },
                    "mentionable": {
                        "type": "boolean",
                        "description": "Whether the role can be mentioned"
                    },
                    "permissions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of permission names to grant (e.g. 'view_channel', 'send_messages', 'read_message_history')"
                    }
                },
                "required": ["server_id", "name"]
            }
        ),
        Tool(
            name="edit_role_permissions",
            description="Edit a role's server-wide permissions. Use this to change what @everyone or any role can do by default across the server.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {
                        "type": "string",
                        "description": "Discord server ID"
                    },
                    "role_id": {
                        "type": "string",
                        "description": "Role ID to edit (use server ID for @everyone)"
                    },
                    "grant": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Permission names to enable (e.g. 'send_messages', 'read_message_history')"
                    },
                    "deny": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Permission names to disable (e.g. 'view_channel', 'send_messages')"
                    }
                },
                "required": ["server_id", "role_id"]
            }
        ),
        Tool(
            name="set_channel_permission",
            description="Set permission overwrite for a role or user on a specific channel. Allows fine-grained control: grant, deny, or reset individual permissions per channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID to set permissions on"
                    },
                    "target_id": {
                        "type": "string",
                        "description": "Role ID or User ID to set permissions for"
                    },
                    "target_type": {
                        "type": "string",
                        "enum": ["role", "member"],
                        "description": "Whether target is a role or member"
                    },
                    "grant": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Permission names to explicitly allow (e.g. 'view_channel', 'send_messages')"
                    },
                    "deny": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Permission names to explicitly deny"
                    },
                    "reset": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Permission names to reset to inherit from role"
                    }
                },
                "required": ["channel_id", "target_id", "target_type"]
            }
        ),
        Tool(
            name="remove_channel_permission",
            description="Remove all permission overwrites for a role or user on a specific channel (resets to default/inherited)",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "Channel ID to remove permissions from"
                    },
                    "target_id": {
                        "type": "string",
                        "description": "Role ID or User ID to remove overwrites for"
                    },
                    "target_type": {
                        "type": "string",
                        "enum": ["role", "member"],
                        "description": "Whether target is a role or member"
                    }
                },
                "required": ["channel_id", "target_id", "target_type"]
            }
        )
    ]

@app.call_tool()
@require_discord_client
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle Discord tool calls."""
    
    if name == "send_message":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.send(arguments["content"])
        return [TextContent(
            type="text",
            text=f"Message sent successfully. Message ID: {message.id}"
        )]

    elif name == "edit_message":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        await message.edit(content=arguments["content"])
        return [TextContent(
            type="text",
            text=f"Message edited successfully. Message ID: {message.id}"
        )]

    elif name == "read_messages":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        limit = min(int(arguments.get("limit", 10)), 100)
        fetch_users = arguments.get("fetch_reaction_users", False)  # Only fetch users if explicitly requested
        messages = []
        async for message in channel.history(limit=limit):
            reaction_data = []
            for reaction in message.reactions:
                emoji_str = str(reaction.emoji.name) if hasattr(reaction.emoji, 'name') and reaction.emoji.name else str(reaction.emoji.id) if hasattr(reaction.emoji, 'id') else str(reaction.emoji)
                reaction_info = {
                    "emoji": emoji_str,
                    "count": reaction.count
                }
                logger.error(f"Emoji: {emoji_str}")
                reaction_data.append(reaction_info)
            messages.append({
                "id": str(message.id),
                "author": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "reactions": reaction_data  # Add reactions to message dict
            })
        # Helper function to format reactions
        def format_reaction(r):
            return f"{r['emoji']}({r['count']})"
            
        return [TextContent(
            type="text",
            text=f"Retrieved {len(messages)} messages:\n\n" + 
                 "\n".join([
                     f"{m['author']} ({m['timestamp']}): {m['content']}\n" +
                     f"Reactions: {', '.join([format_reaction(r) for r in m['reactions']]) if m['reactions'] else 'No reactions'}"
                     for m in messages
                 ])
        )]

    elif name == "get_user_info":
        user = await discord_client.fetch_user(int(arguments["user_id"]))
        user_info = {
            "id": str(user.id),
            "name": user.name,
            "discriminator": user.discriminator,
            "bot": user.bot,
            "created_at": user.created_at.isoformat()
        }
        return [TextContent(
            type="text",
            text=f"User information:\n" + 
                 f"Name: {user_info['name']}#{user_info['discriminator']}\n" +
                 f"ID: {user_info['id']}\n" +
                 f"Bot: {user_info['bot']}\n" +
                 f"Created: {user_info['created_at']}"
        )]

    elif name == "moderate_message":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        
        # Delete the message
        await message.delete()
        
        # Handle timeout if specified
        if "timeout_minutes" in arguments and arguments["timeout_minutes"] > 0:
            if isinstance(message.author, discord.Member):
                duration = discord.utils.utcnow() + datetime.timedelta(
                    minutes=arguments["timeout_minutes"]
                )
                await message.author.timeout(
                    duration,
                    reason=arguments["reason"]
                )
                return [TextContent(
                    type="text",
                    text=f"Message deleted and user timed out for {arguments['timeout_minutes']} minutes."
                )]
        
        return [TextContent(
            type="text",
            text="Message deleted successfully."
        )]

    # Server Information Tools
    elif name == "get_server_info":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        info = {
            "name": guild.name,
            "id": str(guild.id),
            "owner_id": str(guild.owner_id),
            "member_count": guild.member_count,
            "created_at": guild.created_at.isoformat(),
            "description": guild.description,
            "premium_tier": guild.premium_tier,
            "explicit_content_filter": str(guild.explicit_content_filter)
        }
        return [TextContent(
            type="text",
            text=f"Server Information:\n" + "\n".join(f"{k}: {v}" for k, v in info.items())
        )]

    elif name == "get_channels":
        try:
            guild = discord_client.get_guild(int(arguments["server_id"]))
            if guild:
                channel_list = []
                for channel in guild.channels:
                    channel_list.append(f"#{channel.name} (ID: {channel.id}) - {channel.type}")
                
                return [TextContent(
                    type="text", 
                    text=f"Channels in {guild.name}:\n" + "\n".join(channel_list)
                )]
            else:
                return [TextContent(type="text", text="Guild not found")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "list_members":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        limit = min(int(arguments.get("limit", 100)), 1000)
        
        members = []
        async for member in guild.fetch_members(limit=limit):
            members.append({
                "id": str(member.id),
                "name": member.name,
                "nick": member.nick,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "roles": [str(role.id) for role in member.roles[1:]]  # Skip @everyone
            })
        
        return [TextContent(
            type="text",
            text=f"Server Members ({len(members)}):\n" + 
                 "\n".join(f"{m['name']} (ID: {m['id']}, Roles: {', '.join(m['roles'])})" for m in members)
        )]

    # Role Management Tools
    elif name == "add_role":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        member = await guild.fetch_member(int(arguments["user_id"]))
        role = guild.get_role(int(arguments["role_id"]))
        
        await member.add_roles(role, reason="Role added via MCP")
        return [TextContent(
            type="text",
            text=f"Added role {role.name} to user {member.name}"
        )]

    elif name == "remove_role":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        member = await guild.fetch_member(int(arguments["user_id"]))
        role = guild.get_role(int(arguments["role_id"]))
        
        await member.remove_roles(role, reason="Role removed via MCP")
        return [TextContent(
            type="text",
            text=f"Removed role {role.name} from user {member.name}"
        )]

    # Channel Management Tools
    elif name == "create_text_channel":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        category = None
        if "category_id" in arguments:
            category = guild.get_channel(int(arguments["category_id"]))
        
        channel = await guild.create_text_channel(
            name=arguments["name"],
            category=category,
            topic=arguments.get("topic"),
            reason="Channel created via MCP"
        )
        
        return [TextContent(
            type="text",
            text=f"Created text channel #{channel.name} (ID: {channel.id})"
        )]

    elif name == "delete_channel":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        await channel.delete(reason=arguments.get("reason", "Channel deleted via MCP"))
        return [TextContent(
            type="text",
            text=f"Deleted channel successfully"
        )]

    # Message Reaction Tools
    elif name == "add_reaction":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        await message.add_reaction(arguments["emoji"])
        return [TextContent(
            type="text",
            text=f"Added reaction {arguments['emoji']} to message"
        )]

    elif name == "add_multiple_reactions":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        for emoji in arguments["emojis"]:
            await message.add_reaction(emoji)
        return [TextContent(
            type="text",
            text=f"Added reactions: {', '.join(arguments['emojis'])} to message"
        )]

    elif name == "remove_reaction":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        message = await channel.fetch_message(int(arguments["message_id"]))
        await message.remove_reaction(arguments["emoji"], discord_client.user)
        return [TextContent(
            type="text",
            text=f"Removed reaction {arguments['emoji']} from message"
        )]

    elif name == "list_servers":
        servers = []
        for guild in discord_client.guilds:
            servers.append({
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
                "created_at": guild.created_at.isoformat()
            })
        
        return [TextContent(
            type="text",
            text=f"Available Servers ({len(servers)}):\n" + 
                 "\n".join(f"{s['name']} (ID: {s['id']}, Members: {s['member_count']})" for s in servers)
        )]

    # Server Structure Tools
    elif name == "create_category":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        category = await guild.create_category(
            name=arguments["name"],
            reason="Category created via MCP"
        )
        return [TextContent(
            type="text",
            text=f"Created category '{category.name}' (ID: {category.id})"
        )]

    elif name == "create_forum_channel":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        category = None
        if "category_id" in arguments:
            category = guild.get_channel(int(arguments["category_id"]))

        # Build default tags if provided
        available_tags = []
        if "tags" in arguments and arguments["tags"]:
            for tag_name in arguments["tags"]:
                available_tags.append(discord.ForumTag(name=tag_name))

        forum = await guild.create_forum(
            name=arguments["name"],
            category=category,
            topic=arguments.get("topic"),
            default_auto_archive_duration=10080,
            reason="Forum created via MCP"
        )

        # Add tags after creation if provided
        if available_tags:
            await forum.edit(available_tags=available_tags)

        return [TextContent(
            type="text",
            text=f"Created forum channel #{forum.name} (ID: {forum.id})"
        )]

    elif name == "move_channel":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        category = None
        if "category_id" in arguments:
            category = await discord_client.fetch_channel(int(arguments["category_id"]))
        await channel.edit(category=category, reason="Channel moved via MCP")
        target = category.name if category else "no category"
        return [TextContent(
            type="text",
            text=f"Moved #{channel.name} to category '{target}'"
        )]

    # Forum Channel Tools
    elif name == "get_forum_posts":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        if not isinstance(channel, discord.ForumChannel):
            return [TextContent(type="text", text=f"Channel {arguments['channel_id']} is not a forum channel (type: {type(channel).__name__})")]

        posts = []

        # Active threads (cached)
        for thread in channel.threads:
            tag_names = []
            for tag_id in thread.applied_tags:
                for available_tag in channel.available_tags:
                    if available_tag.id == tag_id.id if hasattr(tag_id, 'id') else tag_id == available_tag.id:
                        tag_names.append(available_tag.name)
            posts.append({
                "id": str(thread.id),
                "title": thread.name,
                "author_id": str(thread.owner_id),
                "created_at": thread.created_at.isoformat() if thread.created_at else "unknown",
                "message_count": thread.message_count,
                "tags": tag_names,
                "archived": thread.archived,
                "locked": thread.locked
            })

        # Archived threads
        async for thread in channel.archived_threads(limit=100):
            # Skip if already listed from active threads
            if any(p["id"] == str(thread.id) for p in posts):
                continue
            tag_names = []
            for tag_id in thread.applied_tags:
                for available_tag in channel.available_tags:
                    if available_tag.id == tag_id.id if hasattr(tag_id, 'id') else tag_id == available_tag.id:
                        tag_names.append(available_tag.name)
            posts.append({
                "id": str(thread.id),
                "title": thread.name,
                "author_id": str(thread.owner_id),
                "created_at": thread.created_at.isoformat() if thread.created_at else "unknown",
                "message_count": thread.message_count,
                "tags": tag_names,
                "archived": thread.archived,
                "locked": thread.locked
            })

        return [TextContent(
            type="text",
            text=f"Forum posts in #{channel.name} ({len(posts)} posts):\n\n" +
                 "\n".join([
                     f"- **{p['title']}** (ID: {p['id']})\n"
                     f"  Author ID: {p['author_id']} | Created: {p['created_at']}\n"
                     f"  Messages: {p['message_count']} | Tags: {', '.join(p['tags']) if p['tags'] else 'None'}\n"
                     f"  Archived: {p['archived']} | Locked: {p['locked']}"
                     for p in posts
                 ]) if posts else "No posts found."
        )]

    elif name == "read_forum_post":
        thread = await discord_client.fetch_channel(int(arguments["thread_id"]))
        limit = min(int(arguments.get("limit", 50)), 100)

        messages = []
        async for message in thread.history(limit=limit):
            messages.append({
                "id": str(message.id),
                "author": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat()
            })

        return [TextContent(
            type="text",
            text=f"Messages in thread '{thread.name}' ({len(messages)} messages):\n\n" +
                 "\n".join([
                     f"{m['author']} ({m['timestamp']}): {m['content']}"
                     for m in messages
                 ])
        )]

    elif name == "create_forum_post":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        if not isinstance(channel, discord.ForumChannel):
            return [TextContent(type="text", text=f"Channel {arguments['channel_id']} is not a forum channel")]

        # Match tag names to available tags
        applied_tags = []
        if "tag_names" in arguments and arguments["tag_names"]:
            for tag_name in arguments["tag_names"]:
                for available_tag in channel.available_tags:
                    if available_tag.name.lower() == tag_name.lower():
                        applied_tags.append(available_tag)
                        break

        thread_with_message = await channel.create_thread(
            name=arguments["title"],
            content=arguments["content"],
            applied_tags=applied_tags
        )

        return [TextContent(
            type="text",
            text=f"Created forum post '{arguments['title']}' (Thread ID: {thread_with_message.thread.id})"
        )]

    elif name == "get_forum_tags":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        if not isinstance(channel, discord.ForumChannel):
            return [TextContent(type="text", text=f"Channel {arguments['channel_id']} is not a forum channel")]

        tags = []
        for tag in channel.available_tags:
            tags.append({
                "id": str(tag.id),
                "name": tag.name,
                "emoji": str(tag.emoji) if tag.emoji else None,
                "moderated": tag.moderated
            })

        return [TextContent(
            type="text",
            text=f"Available tags for #{channel.name} ({len(tags)} tags):\n\n" +
                 "\n".join([
                     f"- {t['name']} (ID: {t['id']}) | Emoji: {t['emoji'] or 'None'} | Moderated: {t['moderated']}"
                     for t in tags
                 ]) if tags else "No tags available."
        )]

    elif name == "add_tags_to_post":
        thread = await discord_client.fetch_channel(int(arguments["thread_id"]))
        parent = thread.parent
        if not isinstance(parent, discord.ForumChannel):
            return [TextContent(type="text", text=f"Thread's parent is not a forum channel")]

        # Get current tags
        existing_tags = list(thread.applied_tags)

        # Match new tag names to available tags
        new_tags = []
        not_found = []
        for tag_name in arguments["tag_names"]:
            found = False
            for available_tag in parent.available_tags:
                if available_tag.name.lower() == tag_name.lower():
                    # Only add if not already applied
                    if not any(t.id == available_tag.id for t in existing_tags):
                        new_tags.append(available_tag)
                    found = True
                    break
            if not found:
                not_found.append(tag_name)

        all_tags = existing_tags + new_tags
        await thread.edit(applied_tags=all_tags)

        final_tag_names = [t.name for t in all_tags]
        result = f"Updated tags on '{thread.name}': {', '.join(final_tag_names)}"
        if not_found:
            result += f"\nTags not found: {', '.join(not_found)}"

        return [TextContent(type="text", text=result)]

    elif name == "send_file":
        import os as _os
        file_path = arguments["file_path"]
        if not _os.path.isfile(file_path):
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        filename = arguments.get("filename") or _os.path.basename(file_path)
        file = discord.File(file_path, filename=filename)
        content = arguments.get("content", "")
        message = await channel.send(content=content or None, file=file)
        return [TextContent(
            type="text",
            text=f"File '{filename}' sent successfully. Message ID: {message.id}"
        )]

    # Permission Management Tools
    elif name == "get_roles":
        guild = discord_client.get_guild(int(arguments["server_id"]))
        if not guild:
            guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        roles = []
        for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
            perms = [perm for perm, value in role.permissions if value]
            roles.append({
                "id": str(role.id),
                "name": role.name,
                "color": str(role.color),
                "position": role.position,
                "mentionable": role.mentionable,
                "hoist": role.hoist,
                "permissions": perms
            })
        return [TextContent(
            type="text",
            text=f"Roles in {guild.name} ({len(roles)}):\n\n" +
                 "\n".join([
                     f"- **{r['name']}** (ID: {r['id']})\n"
                     f"  Color: {r['color']} | Position: {r['position']} | Hoist: {r['hoist']} | Mentionable: {r['mentionable']}\n"
                     f"  Permissions: {', '.join(r['permissions']) if r['permissions'] else 'None'}"
                     for r in roles
                 ])
        )]

    elif name == "create_role":
        guild = await discord_client.fetch_guild(int(arguments["server_id"]))

        # Build permissions
        perms = discord.Permissions.none()
        if "permissions" in arguments and arguments["permissions"]:
            for perm_name in arguments["permissions"]:
                if hasattr(perms, perm_name):
                    setattr(perms, perm_name, True)

        # Build color
        color = discord.Color.default()
        if "color" in arguments:
            color = discord.Color(int(arguments["color"].lstrip('#'), 16))

        role = await guild.create_role(
            name=arguments["name"],
            permissions=perms,
            color=color,
            hoist=arguments.get("hoist", False),
            mentionable=arguments.get("mentionable", False),
            reason="Role created via MCP"
        )
        return [TextContent(
            type="text",
            text=f"Created role '{role.name}' (ID: {role.id})"
        )]

    elif name == "edit_role_permissions":
        guild = discord_client.get_guild(int(arguments["server_id"]))
        if not guild:
            guild = await discord_client.fetch_guild(int(arguments["server_id"]))
        role = guild.get_role(int(arguments["role_id"]))
        if not role:
            return [TextContent(type="text", text=f"Role {arguments['role_id']} not found")]

        # Start with current permissions
        perms = discord.Permissions(role.permissions.value)

        granted = []
        denied = []

        if "grant" in arguments and arguments["grant"]:
            for perm_name in arguments["grant"]:
                if hasattr(perms, perm_name):
                    setattr(perms, perm_name, True)
                    granted.append(perm_name)

        if "deny" in arguments and arguments["deny"]:
            for perm_name in arguments["deny"]:
                if hasattr(perms, perm_name):
                    setattr(perms, perm_name, False)
                    denied.append(perm_name)

        await role.edit(permissions=perms, reason="Permissions edited via MCP")

        result = f"Updated permissions for role '{role.name}':"
        if granted:
            result += f"\n  Granted: {', '.join(granted)}"
        if denied:
            result += f"\n  Denied: {', '.join(denied)}"
        return [TextContent(type="text", text=result)]

    elif name == "set_channel_permission":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        guild = channel.guild

        # Resolve target
        if arguments["target_type"] == "role":
            target = guild.get_role(int(arguments["target_id"]))
            if not target:
                return [TextContent(type="text", text=f"Role {arguments['target_id']} not found")]
        else:
            target = await guild.fetch_member(int(arguments["target_id"]))

        # Build overwrite from existing or create new
        overwrite = channel.overwrites_for(target)

        granted = []
        denied_perms = []
        reset_perms = []

        if "grant" in arguments and arguments["grant"]:
            for perm_name in arguments["grant"]:
                if hasattr(discord.Permissions, perm_name):
                    setattr(overwrite, perm_name, True)
                    granted.append(perm_name)

        if "deny" in arguments and arguments["deny"]:
            for perm_name in arguments["deny"]:
                if hasattr(discord.Permissions, perm_name):
                    setattr(overwrite, perm_name, False)
                    denied_perms.append(perm_name)

        if "reset" in arguments and arguments["reset"]:
            for perm_name in arguments["reset"]:
                if hasattr(discord.Permissions, perm_name):
                    setattr(overwrite, perm_name, None)
                    reset_perms.append(perm_name)

        await channel.set_permissions(target, overwrite=overwrite, reason="Permissions set via MCP")

        target_name = target.name if hasattr(target, 'name') else str(target)
        result = f"Updated channel permissions for '{target_name}' on #{channel.name}:"
        if granted:
            result += f"\n  Allowed: {', '.join(granted)}"
        if denied_perms:
            result += f"\n  Denied: {', '.join(denied_perms)}"
        if reset_perms:
            result += f"\n  Reset: {', '.join(reset_perms)}"
        return [TextContent(type="text", text=result)]

    elif name == "remove_channel_permission":
        channel = await discord_client.fetch_channel(int(arguments["channel_id"]))
        guild = channel.guild

        if arguments["target_type"] == "role":
            target = guild.get_role(int(arguments["target_id"]))
            if not target:
                return [TextContent(type="text", text=f"Role {arguments['target_id']} not found")]
        else:
            target = await guild.fetch_member(int(arguments["target_id"]))

        await channel.set_permissions(target, overwrite=None, reason="Permission overwrite removed via MCP")
        target_name = target.name if hasattr(target, 'name') else str(target)
        return [TextContent(
            type="text",
            text=f"Removed all permission overwrites for '{target_name}' on #{channel.name}"
        )]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Start Discord bot in the background
    asyncio.create_task(bot.start(DISCORD_TOKEN))
    
    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
