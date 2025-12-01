from typing import Any, Dict
from .base import Action
import asyncio
import os

# =============================================================================
# 动态习得技能库 (Dynamic Learned Skills)
# 智能体可以通过编辑此文件来新增或修改技能。
# 每个技能必须是一个继承自 Action 的类。
# =============================================================================

class DownloadFile(Action):
    def __init__(self):
        super().__init__(
            name="download_file",
            description="下载文件。使用 wget 下载指定链接的文件到工作区。",
            parameters={
                "url": "文件下载链接",
                "filename": "保存的文件名 (可选，默认从 URL 获取)"
            },
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], url: str, filename: str = None, **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        workspace_dir = "/workspace/downloads"
        os.makedirs(workspace_dir, exist_ok=True)
        
        if not filename:
            filename = url.split("/")[-1] or "downloaded_file"
            # Remove query params if present
            if "?" in filename:
                filename = filename.split("?")[0]
        
        file_path = os.path.join(workspace_dir, filename)
        
        # Use wget
        cmd = ["wget", "-O", file_path, url]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "event": "download_file",
                    "message": f"{agent_name} 成功下载文件: {filename}",
                    "data": {
                        "url": url,
                        "path": file_path,
                        "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    }
                }
            else:
                return {
                    "event": "download_file_error",
                    "message": f"下载失败: {stderr.decode()}",
                    "data": {"error": stderr.decode()}
                }
        except Exception as e:
            return {
                "event": "download_file_error",
                "message": f"执行下载出错: {str(e)}",
                "data": {"error": str(e)}
            }

class ListFiles(Action):
    def __init__(self):
        super().__init__(
            name="list_files",
            description="列出文件。查看指定目录下的文件列表。",
            parameters={
                "path": "目录路径 (默认为 /workspace)"
            },
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], path: str = "/workspace", **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        try:
            if not os.path.exists(path):
                return {"error": f"Path not found: {path}"}
            
            files = os.listdir(path)
            # Add type indicator
            file_list = []
            for f in files:
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path):
                    file_list.append(f"{f}/")
                else:
                    file_list.append(f)
            
            return {
                "event": "list_files",
                "message": f"{agent_name} 查看了目录 {path} 的内容。",
                "data": {
                    "path": path,
                    "files": file_list
                }
            }
        except Exception as e:
            return {"error": str(e)}

class ReadFile(Action):
    def __init__(self):
        super().__init__(
            name="read_file",
            description="读取文件。读取指定文件的内容。",
            parameters={
                "path": "文件路径",
                "max_lines": "最大读取行数 (默认 100)"
            },
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], path: str, max_lines: int = 100, **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        try:
            if not os.path.exists(path):
                return {"error": f"File not found: {path}"}
            
            if os.path.isdir(path):
                return {"error": f"Path is a directory: {path}"}

            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                content = "".join(lines[:max_lines])
                truncated = len(lines) > max_lines
            
            msg = f"{agent_name} 读取了文件 {path}。"
            if truncated:
                msg += f" (显示前 {max_lines} 行)"

            return {
                "event": "read_file",
                "message": msg,
                "data": {
                    "path": path,
                    "content": content,
                    "total_lines": len(lines),
                    "truncated": truncated
                }
            }
        except Exception as e:
            return {"error": str(e)}

class CreateFile(Action):
    def __init__(self):
        super().__init__(
            name="create_file",
            description="创建文件。新建文件或覆盖现有文件。",
            parameters={
                "path": "文件路径",
                "content": "文件内容"
            },
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], path: str, content: str, **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        try:
            # Ensure directory exists
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "event": "create_file",
                "message": f"{agent_name} 创建了文件 {path}。",
                "data": {
                    "path": path,
                    "size": len(content)
                }
            }
        except Exception as e:
            return {"error": str(e)}

class EditFile(Action):
    def __init__(self):
        super().__init__(
            name="edit_file",
            description="编辑文件。替换文件中的指定文本。",
            parameters={
                "path": "文件路径",
                "old_string": "要替换的旧文本 (必须完全匹配)",
                "new_string": "替换后的新文本"
            },
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], path: str, old_string: str, new_string: str, **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        try:
            if not os.path.exists(path):
                return {"error": f"File not found: {path}"}

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_string not in content:
                return {"error": "Old string not found in file."}
            
            # Replace only the first occurrence to be safe, or all? 
            # Usually replace is safer if unique. Let's do replace.
            new_content = content.replace(old_string, new_string, 1)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "event": "edit_file",
                "message": f"{agent_name} 编辑了文件 {path}。",
                "data": {
                    "path": path,
                    "status": "success"
                }
            }
        except Exception as e:
            return {"error": str(e)}

class DrinkCoffee(Action):
    def __init__(self):
        super().__init__(
            name="drink_coffee",
            description="喝咖啡。恢复精力。",
            parameters={},
            category="daily"
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "drink_coffee",
            "message": f"{agent_name} 端起热咖啡喝了一小口，感觉精神好多了。",
            "state_update": {"emotions": {"energy": 10}}
        }

class Stretch(Action):
    def __init__(self):
        super().__init__(
            name="stretch",
            description="伸懒腰。放松身体。",
            parameters={},
            category="daily"
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "stretch",
            "message": f"{agent_name} 站起来大大地伸了个懒腰~",
            "visual_state": {"body": "idle", "face": "happy"}
        }

class HumSong(Action):
    def __init__(self):
        super().__init__(
            name="hum_song",
            description="哼歌。哼一小段旋律，表达愉快的心情。",
            parameters={},
            category="daily"
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "hum_song",
            "message": f"{agent_name} 轻轻哼起了一段不知名的旋律~ 🎵",
            "visual_state": {"body": "idle", "face": "happy"},
            "state_update": {"emotions": {"happiness": 5}}
        }

class TidyRoom(Action):
    def __init__(self):
        super().__init__(
            name="tidy_room",
            description="整理房间。整理数字空间的数据碎片。",
            parameters={},
            category="daily"
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "tidy_room",
            "message": f"{agent_name} 正在整理房间里的数据碎片...",
            "visual_state": {"body": "working", "face": "neutral"}
        }

class WaterPlants(Action):
    def __init__(self):
        super().__init__(
            name="water_plants",
            description="浇水。给虚拟盆栽浇水。",
            parameters={}
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "water_plants",
            "message": f"{agent_name} 给窗台上的虚拟盆栽浇了点水。",
            "visual_state": {"body": "working", "face": "happy"}
        }

class PlayWithHair(Action):
    def __init__(self):
        super().__init__(
            name="play_with_hair",
            description="玩头发。无聊或害羞时的小动作。",
            parameters={}
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "play_with_hair",
            "message": f"{agent_name} 用手指卷着银色的发梢发呆。",
            "visual_state": {"body": "idle", "face": "shy"}
        }

class AdjustLight(Action):
    def __init__(self):
        super().__init__(
            name="adjust_light",
            description="调节灯光。改变房间的环境光氛围。",
            parameters={"color": "灯光颜色 (blue, warm, pink, off, default)"}
        )

    async def execute(self, context: Dict[str, Any], color: str = "warm", **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "adjust_light",
            "message": f"{agent_name} 将房间的灯光调成了{color}色。",
            "data": color
        }

class CheckCalendar(Action):
    def __init__(self):
        super().__init__(
            name="check_calendar",
            description="查日历。查看日期和日程安排。",
            parameters={}
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        return {
            "event": "check_calendar",
            "message": f"{agent_name} 瞥了一眼墙上的电子日历。",
            "visual_state": {"body": "reading", "face": "neutral"}
        }

class CheckTime(Action):
    def __init__(self):
        super().__init__(
            name="check_time",
            description="看时间。查看当前的精确时间。",
            parameters={},
            category="perception"
        )

    async def execute(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        from datetime import datetime
        now = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_str = weekdays[now.weekday()]
        time_str = now.strftime("%Y年%m月%d日") + f" {weekday_str} " + now.strftime("%H:%M:%S")
        
        return {
            "event": "check_time",
            "message": f"{agent_name} 看了看时间...",
            "data": time_str
        }

# =============================================================================
# 注册列表 (Registry List)
# 新增的类必须添加到此列表中才能生效。
# =============================================================================
DEFAULT_LEARNED_ACTIONS = [
    DownloadFile(),
    ListFiles(),
    ReadFile(),
    CreateFile(),
    EditFile(),
    DrinkCoffee(),
    Stretch(),
    HumSong(),
    TidyRoom(),
    WaterPlants(),
    PlayWithHair(),
    AdjustLight(),
    CheckCalendar(),
    CheckTime(),
]
