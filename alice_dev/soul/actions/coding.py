import sys
import io
import os
import traceback
import re
import importlib
import base64
import asyncio
from typing import Dict, Any
from .base import Action
from . import learned

class ManageSkill(Action):
    def __init__(self, registry):
        self.registry = registry
        super().__init__(
            name="manage_skill",
            description="管理习得技能。用于新增或修改你的技能代码。这允许你改变自己的行为模式。",
            parameters={
                "action_type": "操作类型 ('create', 'update', 'delete')",
                "skill_name": "技能类名 (例如 'PlayGuitar')",
                "code": "完整的 Python 类代码 (必须继承自 Action)"
            },
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], action_type: str, skill_name: str, code: str = "", **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        file_path = "soul/actions/learned.py"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if action_type in ['create', 'update']:
                # Validate code
                if f"class {skill_name}" not in code:
                    return {"error": f"Code must contain class definition for {skill_name}"}
                if "(Action)" not in code:
                    return {"error": "Class must inherit from Action"}

                # Check if class already exists
                pattern = re.compile(r'class\s+' + re.escape(skill_name) + r'\(Action\):.*?(?=\nclass|\n# ===|$)', re.DOTALL)
                match = pattern.search(content)

                if match:
                    # Update existing
                    new_content = content[:match.start()] + code + "\n\n" + content[match.end():]
                else:
                    # Append new before the registry list
                    insert_pos = content.find("# =============================================================================")
                    if insert_pos == -1: insert_pos = content.find("DEFAULT_LEARNED_ACTIONS")
                    
                    # Find the last class end
                    last_class_end = content.rfind("\nclass ", 0, insert_pos)
                    if last_class_end != -1:
                        # Find end of that class? Hard to parse.
                        # Safer: Insert before the Registry List comment block
                        target_marker = "# ============================================================================="
                        parts = content.split(target_marker)
                        if len(parts) >= 2:
                            # Insert at the end of the second to last part (before the registry block)
                            new_content = parts[0] + code + "\n\n" + target_marker + parts[1]
                        else:
                             new_content = content + "\n\n" + code
                    else:
                        new_content = code + "\n\n" + content

                # Update Registry List
                if f"{skill_name}()" not in new_content:
                    # Add to list
                    list_pattern = r"DEFAULT_LEARNED_ACTIONS\s*=\s*\[(.*?)\]"
                    list_match = re.search(list_pattern, new_content, re.DOTALL)
                    if list_match:
                        list_content = list_match.group(1)
                        if skill_name not in list_content:
                            new_list_content = list_content.rstrip() + f",\n    {skill_name}(),"
                            new_content = new_content.replace(list_match.group(1), new_list_content)

                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                # Reload
                importlib.reload(learned)
                self.registry.reload_learned()

                return {
                    "event": "skill_updated",
                    "message": f"{agent_name} 成功更新了技能: {skill_name}",
                    "data": code
                }

            elif action_type == 'delete':
                # Not implemented for safety yet
                return {"error": "Delete not implemented yet"}

        except Exception as e:
            return {"error": f"Failed to manage skill: {str(e)}"}
        
        return {"error": "Invalid action type"}

class RunPython(Action):
    def __init__(self):
        super().__init__(
            name="run_python",
            description="执行 Python 代码。用于计算、数据处理或测试代码片段。支持 matplotlib/seaborn 绘图。",
            parameters={"code": "要执行的 Python 代码"},
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], code: str, **kwargs) -> Dict[str, Any]:
        agent_name = context.get("agent_name", "Alice")
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        
        # Capture images
        images = []
        
        # Setup matplotlib backend if available
        plt = None
        original_show = None
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Configure font for Chinese support
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False
            
            def custom_show():
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                images.append(img_str)
                plt.close()
                
            # Monkeypatch show
            original_show = plt.show
            plt.show = custom_show
        except ImportError:
            pass

        try:
            # Execute code
            exec(code, {}, {})
            output = redirected_output.getvalue()
            
            result_data = {
                "code": code,
                "output": output
            }
            
            if images:
                result_data["images"] = images

            return {
                "event": "run_code",
                "message": f"{agent_name} 执行了一段代码...",
                "data": result_data
            }
        except Exception as e:
            return {
                "event": "run_code_error",
                "message": "代码执行出错",
                "data": {
                    "code": code,
                    "error": traceback.format_exc()
                }
            }
        finally:
            sys.stdout = old_stdout
            if plt and original_show:
                plt.show = original_show

class RunBash(Action):
    def __init__(self):
        super().__init__(
            name="run_bash",
            description="执行 Bash 命令。用于文件操作、系统查询等。",
            parameters={"command": "要执行的 Bash 命令"},
            category="coding"
        )

    async def execute(self, context: Dict[str, Any], command: str, **kwargs) -> Dict[str, Any]:
        try:
            # Ensure workspace directory exists
            workspace_dir = "/workspace"
            if not os.path.exists(workspace_dir):
                os.makedirs(workspace_dir, exist_ok=True)

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_dir
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode().strip()
            error = stderr.decode().strip()
            
            result_msg = f"Output:\n{output}"
            if error:
                result_msg += f"\nError:\n{error}"
                
            return {
                "event": "run_bash",
                "message": f"执行命令: {command}\n{result_msg[:100]}...",
                "data": {
                    "command": command,
                    "output": output,
                    "error": error,
                    "return_code": process.returncode
                }
            }
        except Exception as e:
             return {
                "event": "run_bash_error",
                "message": "命令执行出错",
                "data": {
                    "command": command,
                    "error": str(e)
                }
            }
