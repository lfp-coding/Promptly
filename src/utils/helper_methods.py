from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QPixmap, QIcon
from pynput import keyboard

import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

class HelperMethods:
    """Singleton helper class for methods of main process"""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = HelperMethods()
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._hotkey_listener_running = False

        self._special_keys = {
                keyboard.Key.enter: "enter",
                keyboard.Key.space: "space",
                keyboard.Key.tab: "tab",
                keyboard.Key.backspace: "backspace",
                keyboard.Key.esc: "esc",
                keyboard.Key.shift: "shift",
                keyboard.Key.ctrl: "ctrl",
                keyboard.Key.alt: "alt",
                keyboard.Key.cmd: "cmd",
                keyboard.Key.delete: "delete",
                keyboard.Key.home: "home",
                keyboard.Key.end: "end",
                keyboard.Key.page_up: "page_up",
                keyboard.Key.page_down: "page_down",
                keyboard.Key.left: "left",
                keyboard.Key.right: "right",
                keyboard.Key.up: "up",
                keyboard.Key.down: "down"
        }
        self._shifted_map = {
                    '°': '^', '!': '1', '"': '2', '²': '2', '§': '3', '³': '3', '$': '4', '%': '5', '&': '6', '/': '7',
                    '{': '7', '(': '8', '[': '8', ')': '9', ']': '9', '=': '0', '}': '0', '?': 'ß', '\\': 'ß', '`': '´',
                    '@': 'q', '€': 'e', '*': '+', '~': '+', '\'': '#', '>': '<', '|': '<', ';': ',', ':': '.', '_': '-'
        }

        self._vk_map = {
            # Alphanumeric keys (ASCII-compatible)
            **{i: chr(i) for i in range(0x30, 0x3A)},  # Numbers 0-9
            **{i: chr(i) for i in range(0x41, 0x5B)},  # Letters A-Z

            # Function keys
            **{i: f"F{i - 0x6F}" for i in range(0x70, 0x88)},  # F1-F24

            # Numpad keys
            **{i + 0x60: f"NumPad {i}" for i in range(10)},  # NumPad digits 0-9
            0x6A: "NumPad *",
            0x6B: "NumPad +",
            0x6C: "NumPad Separator",
            0x6D: "NumPad -",
            0x6E: "NumPad .",
            0x6F: "NumPad /",

            # Modifier keys
            0x10: "Shift",
            0x11: "Control",
            0x12: "Alt",

            # Lock keys
            0x14: "Caps Lock",
            0x90: "Num Lock",
            0x91: "Scroll Lock",

            # Navigation keys
            0x1B: "Escape",
            0x20: "Spacebar",
            0x21: "Page Up",
            0x22: "Page Down",
            0x23: "End",
            0x24: "Home",
            0x25: "Left Arrow",
            0x26: "Up Arrow",
            0x27: "Right Arrow",
            0x28: "Down Arrow",

            # Editing keys
            0x08: "Backspace",
            0x09: "Tab",
            0x2C: "Print Screen",
            0x2D: "Insert",
            0x2E: "Delete",

            # Windows and Application keys
            0x5B: "Left Windows Key",
            0x5C: "Right Windows Key",
            0x5D: "Applications Key",

            # OEM and special characters (US keyboard layout)
            0xBA: ";", 
            0xBB: "=",
            0xBC: ",", 
            0xBD: "-", 
            0xBE: ".", 
            0xBF: "/", 
            0xC0: "`", 
            
            # Brackets and backslash
            0xDB: "[", 
            0xDC: "\\", 
            0xDD: "]", 
            
            # Quotes
            0xDE: "'"
        }
    def update(self, hotkey_listener_running):
        """"
        Updates self._hotkey_listener_running variable
        """
        self._hotkey_listener_running = hotkey_listener_running

    def get_hotkey_listener_status(self) -> bool:
        """
        Return:
            bool:
                True: If hotkey listener is running
                False: Otherwise
        """
        return self._hotkey_listener_running
    
    def key_to_string(self, key):
        """
        Convert a pynput key object to a normalized string representation.
        
        Args:
            key: The pynput key object (Key or KeyCode).
        
        Returns:
            str: The string representation of the key.
        """
        # Handle special keys (e.g., modifiers, function keys)
        if isinstance(key, keyboard.Key):
            key_name = key.name
            if key_name in ['ctrl_l', 'ctrl_r']:
                return "ctrl"
            elif key_name in ['alt_l', 'alt_r']:
                return "alt"
            elif key_name in ['shift_l', 'shift_r']:
                return "shift"
            elif key_name in ['cmd', 'cmd_r', 'cmd_l', 'win']:
                return "cmd"
            return self._special_keys.get(key, f"{key.name}")
        
        # Handle character keys
        elif isinstance(key, keyboard.KeyCode):
            if key.char is not None:
                # Handle shifted characters
                if key.char in self._shifted_map:
                    return f"{self._shifted_map[key.char]}"
            
            if key.vk is not None:
            # elif key.vk is not None:
                # Map virtual key codes for non-character keys
                return f"{self._vk_map.get(key.vk, f'vk_{key.vk}')}"
        
        # Default fallback for unmappable keys
        return None

    def get_icon(self):
        # Decode Base64 string and create an icon
        icon_base64 = """
        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zP/Nysr/zMjI/8vHx//Lx8f/zMjI/83IyP/Nycn/zcnJ/83Jyf/Oysr/zsrK/87Kyv/Oysr/zsrL/8/Ly//b2Nj/2tjY/9nX1//Z19f/2dbW/9nW1f/Z1dX/2NXV/9jV1f/Y1NX/19PT/9bT0v/W0tP/1dHS/9LP0P/PzMz/zMjJ/8nGxv/HxMT/yMTE/8nFxf/Lx8f/zMfI/83IyP/NyMn/zsjJ/83Iyf/Nycn/zsnK/87Jyv/Oycr/z8rK/9vY2P/a2Nj/2tfX/9nX1//Z19f/2dbW/9nV1f/Z1NX/2dXV/9jV1f/Y1NT/1tPT/9XS0v/T0dH/z83N/8rHx//Gw8P/w8DA/8K/v//FwcH/yMTE/8rGxv/Lx8f/zMjI/83IyP/NyMn/zcjJ/87Jyf/Nycn/zcnJ/87Jyv/Oycr/29nZ/9rY2P/a19j/2tfX/9rX1//Z1tf/2dbW/9nV1f/Z1dX/2dXV/9jU1f/W1NT/1NLS/9DOzv/Gw8P/v7y8/7y4uP+7t7f/vbm6/8O/v//Hw8T/ysXG/8rGxv/Kxsb/y8fH/8zIyP/MyMj/zcnJ/83Jyf/Nycn/zsnK/87Kyv/c2dn/29jZ/9rY2P/a2Nj/2tfX/9nX1//Z1tf/2dbW/9nV1v/Z1dX/2NXV/9jW1v/U0tL/vru7/7CsrP+sqaj/rKio/7Ktrf+6trb/wr6+/8bCw//IxMT/yMTE/8nFxP/KxcX/ysbG/8vHx//MyMj/zcnJ/83Jyf/Nycr/zsrK/93Z2v/c2Nn/29jY/9vY2P/b19f/2tfX/9rX1//a1tf/2dbW/9jX1//a2Nj/2NbW/6unpv+Mhob/iYKC/4mCgv+alZX/raip/7m0tf/BvLz/w7/A/8TAwP/FwMH/xsLC/8jDw//JxMT/ysbG/8zHyP/NyMj/zcnJ/87Jyv/Oysr/3drb/9zZ2v/c2dn/29jZ/9vY2P/a19f/2dfX/9nX1//Z19f/19XV/+Tk5P+6s7H/RCsj/zkiHP8xHBf/T0A7/5SPj/+rpqf/trKy/7q2t/+9uLn/vrq6/8C7vP/Cvr7/xcDB/8fDw//KxcX/y8jI/8zIyf/Nycn/zsrK/8/Kyv/e2tv/3dna/9zZ2f/c2Nn/3NjZ/9vY2P/a19j/2tfY/9jX1//Y1tb/6enp/7euq/9EKR//komH/0c7Of89LCj/lY+P/6ahov+tqKn/r6ur/7Ktrv+2sbH/ura2/766uv/Cvr//xsLC/8rFxf/Mx8f/zcjI/83Kyv/Oysr/zsrK/97b2//e2tv/3dra/93Z2f/c2dn/3NjZ/9vX2P/a2Nj/2djY/9rY1//r6uv/ua+s/04zKf/v7e3/cmtp/zsrJv+Oior/lZGR/5mUlf+emZn/pqGh/6yoqf+0sLD/u7a3/8G9vf/GwsL/ysXG/8zIx//Nycn/zcrK/87Kyv/Oy8v/39vc/9/a2//d2tv/3Nra/9zZ2f/c2Nn/29jZ/9vY2P/a2Nj/2tjY/+zs7P+5sK3/TjMp/+Lf3/9rYmD/KhQO/1FCPv9TRUH/bWNg/4aAgP+VkJD/pJ+e/6+qqv+4tLT/wby9/8fDw//Kxsb/zMjI/83Jyv/Oysv/z8rM/8/LzP/f3Nz/39vb/97a2//d2tr/3dna/9zZ2f/c2dn/29nZ/9vZ2f/b2dn/7ezt/7qxrv9QNSv/4t/e/4qEhP9CMzH/TT88/zUmIv8bCQX/Sj05/4F7ev+Zk5P/q6am/7izs//Cvb7/yMTF/8vIyP/Nycr/z8rM/8/KzP/Pysz/0MvM/9/c3P/e29z/3tvb/93a2//d2tr/3dna/9zZ2f/c2dn/3NnZ/9za2v/u7e3/u7Ku/1Q5L//Z1dT/397e/9vY2P/b2dn/3t3e/4aBgv8XBwT/VEhF/5KNjf+oo6T/ubS1/8TAwP/Lx8f/zcnK/8/KzP/Qy83/0MvN/9DLzf/QzM3/3tzc/97c3P/e3Nz/3dvb/93a2v/d2tr/3dna/9zZ2f/c2tr/3Nra/+7t7v+8sq//Uzcs/+Xi4f+Cenj/TTUs/2BHPP+AbGP/7Ovq/2liYv8nFRD/ioSD/6unqP++urr/ycXF/87Jyv/Qy83/0MzO/9DNzv/Rzc7/0czO/9HMzv/f29z/3tzc/97c3P/e29v/3trb/93a2v/d2dr/3dna/9za2v/c2tr/7u3u/7yzsP9TOC3/5+Tk/3dubP83HRT/UDYs/z0gE/+0qKP/r62u/yMPCv+Hfnz/trOz/8bDw//Pysv/0MzN/9LNzv/Rzs7/0s7O/9HOz//Rzs7/0c3O/9/b3P/f3Nz/3tzc/97b2//e29v/3trb/93a2v/d2dr/3dra/93a2v/u7e7/vbSw/1Q5Lv/n5OT/cWdl/ykPBv9BJx3/OBwR/8G5tv+opaX/LhcQ/5mSkf/Ixcb/z8vN/9LNz//Tzs//087Q/9POz//SztD/0s7P/9LOz//Rzc7/4N3d/9/b3P/f3Nz/39zc/97b3P/e29v/3trb/93Z2v/d29v/3dva/+3t7v+9s7D/Vjsx/+nn5/+moqL/bmRi/3NpZv+knZv/6+vt/11LRf9ROzP/xcPE/9LP0P/Tz9D/1NDQ/9PQ0f/U0NH/1NDQ/9PP0P/Tzs//0s3P/9LNz//g3d7/4Nzd/+Db3P/f29z/3tvc/97b3P/e29v/3trb/97b2//c29v/7Ozt/72zsP9UOS7/v7Wy/9DJx//Sy8r/0cvJ/8K5t/9nUUr/QSYb/7Osqv/Z2dn/0tDQ/9TS0v/U0tL/1NLR/9TS0f/U0dH/09DR/9PP0P/Szs//0s3P/+Hd3v/g3d3/39zc/9/b3P/f3Nz/39vc/97b2//e2tv/3tvc/9zb2v/q6uv/wLe0/1E1Kv9WOzH/Ujcs/1A1K/9PNCr/SzAl/2pUTP/Evr3/4eLi/9TT0v/V1NP/1NTS/9XT0v/U09L/1NLR/9TS0f/T0dH/0tDQ/9PP0P/TztD/4N3e/+Hd3f/g3N3/39vc/9/b3P/f29z/39vc/97b3P/e29z/3dzc/+Dg3//f3dz/1c/O/9fS0P/X0tD/19LQ/9fR0P/c2Nf/7Ozt/+Xm5f/Y19b/19bW/9XV1P/U1NP/1NPS/9XT0v/U09L/1NLR/9TR0f/T0dH/09DQ/9PP0P/h3d7/4d3d/+Dd3v/g3N3/39vc/9/c3P/e3Nz/3tvc/97b3P/e29z/3dzc/+De3//k5OT/5eXl/+Xl5f/l5eX/5eTl/+Li4v/a2tr/2NjX/9rX1//Y1tb/1dXU/9TV0//V1NP/1dPS/9XT0v/V0tL/1dLR/9TR0f/T0NH/08/Q/+He3v/h3d7/4N3d/+Dd3f/g3Nz/3tzc/97c3P/e29z/39vb/97a2//e29z/3dvb/9za2v/b2tn/2trZ/9na2f/Z2dj/2djY/9rY2P/a19f/2dbW/9nV1v/W1dX/1dXU/9XU0//V09L/1dPS/9XS0v/V0tL/1NHR/9TQ0f/T0ND/4d/f/+He3v/h3d3/4N3d/9/d3f/f3Nz/3tzc/97c3P/e29z/3trb/97a2//d2tr/3dna/9zZ2v/b2dn/29jY/9vX1//a1tf/2tfW/9rW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1f/W1NT/19PT/9bT0//W09P/1tLT/9XR0//V0dP/1dHS/9XQ0v/U0NH/0s/R/9LO0P/SzdD/0s3P/9HNzf/QzMz/z8zL/87Ly//Oy8r/zcrK/83Kyv/Ny8r/zsrK/8/Kyv/Pysr/z8vL/8/Ly//Oy8v/z8vL/8/Ly//Py8v/z8vL/8/Ly//Py8v/0MzL/9DMy//a19j/2tfY/9nX1//Z19f/2dbW/9nW1f/Z1tX/2dTV/9nU1f/Z1db/2NXV/9jV1f/X1dX/19TU/9bT0//V09P/1tPT/9XS0//V0tP/1dHS/9XQ0v/U0NL/08/R/9PO0P/Szs//0c3N/9DMzP/Oy8r/zcrK/83Jyf/Nycn/zcnJ/83JyP/Nycn/zcnJ/83Jyf/Oysr/zsrK/83Kyv/Oysr/zsvK/8/Lyv/Py8v/zsvL/8/Ky//Py8v/0MvL/9DLy//a2Nj/2tfY/9rX2P/Z19f/2dbX/9nW1v/Z1tb/2dXV/9nV1f/Z1dX/2dTV/9jV1f/Y1dX/2NTU/9fT0//W09P/1tPT/9XT0//W0tP/1dHS/9TQ0v/Tz9H/08/R/9LO0P/Rzc3/z8vL/83Kyv/Mycj/zMjI/8vIx//LyMj/zMjI/83IyP/NyMj/zcnJ/8zJyf/Nycn/zcnJ/83Kyv/Oysr/zsrK/87Kyv/Oysr/zsrK/87Kyv/Pysv/z8vL/8/Ly//b2Nj/2tjY/9rY2P/Z19f/2dfX/9nW1v/Z1tb/2dbW/9nV1f/Z1dX/2NXV/9jV1f/Y1dX/2NXV/9fU1P/X09P/1tPS/9bT0v/V0tP/1tHT/9TR0v/Tz9H/0s/Q/8/Mzf/Pysv/zcnJ/8vIyP/Kx8b/ysbF/8rGxv/Kxsb/y8fH/8zHyP/MyMj/zcjI/83Iyf/Nycn/zcnJ/83Jyf/Oycn/zcnJ/87Jyv/Nysr/zsrK/87Kyv/Oysr/zsrK/8/Lyv/b2Nj/2tjY/9rY2P/a19j/2dfX/9nX1//Z19f/2dbW/9nW1v/Z1dX/2dXV/9jV1f/Y1dX/2NXV/9jU1f/X1NT/19PT/9bT0v/W09P/1tLT/9TR0v/S0NH/0M3O/87Ly//MyMn/ysbG/8jFxf/Hw8T/xsPD/8fDw//JxcX/ysbG/8vHx//Mx8f/zMjH/83IyP/NyMn/zcjJ/87Iyf/NyMn/zcjJ/83Iyf/Oycn/zsnJ/87Jyf/Oycr/zsrJ/8/Kyv/b2Nj/2tjY/9rY2P/a19f/2tfX/9nX1//Z19f/2dfX/9nW1v/Z1dX/2dXV/9nU1f/Z1dX/2NXV/9jV1f/Y1NT/19PT/9bT0//W09P/1dHS/9PR0f/Rzs//zcvL/8vIyP/IxcX/xcLD/8PBwf/DwMD/xMDA/8bBwv/IxMT/ycbF/8rGxv/Lx8f/zMjH/8zIyP/NyMn/zcjJ/83Iyf/NyMn/zcnI/87Jyv/Oycr/zcnJ/87Jyv/Oycr/zsnK/87Jyv/b2dn/2tjY/9rY2P/a19f/2tfX/9nX1//Z19f/2dfX/9nW1v/Z1tX/2dXV/9nV1f/Z1dX/2NXV/9jV1f/Y1NX/19PU/9bT0//V09P/1NHS/9HP0P/Ny8v/yMbG/8TCwv/Bv7//wLy9/7+8vP+/vLz/wr2+/8XAwP/Hw8P/ycXF/8rGxv/Kxsf/y8fH/8vHx//Mx8j/zMjI/8zIyP/NyMn/zcnJ/87Jyf/Nycn/zcjJ/83Jyf/Oycn/zsnK/87Jyv/b2dn/29nZ/9vY2P/a19j/2tfY/9rX2P/a19f/2dfX/9nX1//Z1tb/2dbW/9nV1f/Z1dX/2dXV/9nV1f/Y1dX/19TV/9bU1P/V09P/09DQ/83Kyv/Fw8L/v7y8/7u4uP+6trb/ubW1/7q1tv+8uLj/wLy8/8XAwP/Hw8P/ycXF/8rFxv/KxsX/ysXF/8rGxv/Lxsf/y8fH/8zIx//MyMj/zMjJ/83Jyf/Nycn/zcnJ/83Jyf/Oycr/zsrK/87Kyv/c2dn/29nZ/9vY2P/a2Nj/2tjY/9rY2P/a19f/2dfX/9nX1//Z1tf/2dbW/9jW1v/Z1tb/2dTV/9nV1f/Z1dX/2NXV/9fU1P/U0tL/zcrK/8C9vP+2srL/sa2t/7Csq/+wq6v/sayt/7WwsP+5tbX/vru7/8O/v//GwsL/yMPE/8nExP/IxMT/ycXE/8nFxf/KxcX/ysbG/8vGxv/Lx8f/zMfI/83IyP/Nycn/zcnJ/83Jyv/Oycr/zsnK/87Jyv/d2dn/3NnZ/9zY2f/a2Nj/2tjY/9rY2P/a19f/2tfX/9rX1//a19f/2tbX/9nW1v/Z1tb/2NbW/9nW1v/a1tb/2NbW/9jW1v/Rzs7/t7Oz/6WgoP+gmpv/npmZ/52ZmP+hnJ3/qaSk/7GsrP+4s7T/vrm6/8K+vv/FwMH/xsLC/8bCwv/GwsP/x8PD/8jDxP/JxMT/ycXF/8rGxf/Kxsb/y8fH/8zIyP/Nycj/zcnJ/83Kyf/Nycr/zsnK/87Kyv/d2dr/3NnZ/9zY2f/b2Nn/29jY/9vY2P/b2Nj/29fX/9rX1//a19f/2dfX/9rW1//a1tb/2NfX/9nX1//Z19f/2tnZ/9jW1v+sp6f/h4GA/4F6ev+AeXn/gXp6/4V+ff+Tjo7/pJ+g/6+qqv+3srP/vbi5/8G8vP/Cvr7/wr+//8O/wP/EwMD/xMDB/8bBwv/HwsP/yMPD/8jExP/Kxcb/y8fH/8zHyP/NyMj/zcnJ/83Jyf/Oycr/zsrK/8/Ky//d2tv/3Nra/9zZ2f/c2dn/29nZ/9vY2f/b2Nj/29fY/9rX1//Z2Nj/2dfX/9nX1v/Z19f/2dfX/9rY2P/Z19f/6Ojo/6mfnf9DKyP/TTYv/0o0Lf9EMCr/Oych/1xOS/+Ri4v/oZ2d/62pqf+2sbL/ura2/7y4uf++ubr/vrq6/7+7vP/BvL3/wr2+/8O/v//FwMH/xsLC/8jExP/JxcX/ysbH/8vIyP/MyMn/zcjJ/83Jyf/Oysr/zsrK/8/Kyv/e2tv/3dra/93Z2v/c2dn/29nZ/9zY2f/c2Nj/29jY/9rX2P/a19j/2tfY/9nX1//Y19f/2NfX/9rY2P/a2Nj/7u3u/6KWk/84HBL/RCoi/ysYE/8kExD/JREL/1NEQP+Pior/oJub/6ynqP+yra7/tLCw/7Wysv+3s7P/uLS0/7u2tv+9ubn/v7q7/8G9vP/Dv7//xcHC/8fDw//JxcX/y8bH/8vIyP/MyMj/zcnJ/83Kyv/Oysr/zsrK/8/Kyv/e2tv/3dra/93Z2v/d2dn/3NjZ/9zY2f/c2Nn/3NjY/9vX2P/b19j/2tfX/9rX2P/Z19f/2dfX/9vZ2f/c2tn/7+/v/6idmf83GQ7/hXZx/8vJyv96dXX/GgcC/1dIRf+Nh4f/nZiY/6ahov+qpab/rKeo/62qqf+wq6v/sq2t/7Wwsf+4tLX/vLe4/766uv/Bvb7/xcDB/8fDwv/JxMX/y8bH/8zIx//NyMj/zcnJ/83Kyv/Oysr/zsrK/87Lyv/e29v/3trb/97a2v/d2tr/3dna/9zZ2f/c2dn/3NjZ/9zY2P/b2Nj/29fY/9rY2P/Z2Nj/2tjY/9za2v/d29v/8O/w/6mdmv82Fwz/mouG//v8/f+TkI//GAYA/1dIRP+GgH//k42M/5iTk/+blpf/n5ub/6Oen/+noqL/q6an/6+rrP+zsLD/ubS0/7y4uP/AvL3/xMDA/8fCw//JxMX/y8fG/8zIx//Nycn/zcnJ/87Jyv/Oysr/zsrK/8/Ly//e29z/3tvb/97a2//d2tv/3Nra/93Z2v/c2dn/3NnZ/9zY2f/b2Nj/29fY/9rY2P/a2Nj/2tjY/93b2//e3Nz/8fDx/6qemv84GQ7/l4iC//Tz9f+Oi4r/GwgD/1ZHQ/94cnL/e3V1/4F7e/+HgID/i4WF/5OOjv+cl5f/o5+f/6qlpv+wq6z/tbGx/7q2t/+/u7z/xL/A/8fDw//JxcX/y8fH/83Iyf/Nycn/zcrK/87Ky//Oysv/z8rL/8/LzP/f29z/39vc/9/a2//e2tv/3dra/9za2v/c2dn/3djZ/9zZ2f/b2dn/29nZ/9rZ2f/b2Nj/29nZ/93c3P/f3dz/8fHy/6qfm/85Gw//mImE//f3+P+Sjo7/Iw4J/0cyLP9JNzL/Sjgy/08+Ov9cUEz/dG1s/4N9fP+OiIj/m5aV/6Wfn/+sp6j/s66v/7m1tv+/u7z/xMDA/8jExP/Kxsb/y8fI/8zJyf/Oycr/zsrL/87KzP/Pysz/z8rM/8/LzP/f29z/3tvc/9/b2//e2tv/3dra/9za2v/d2dr/3NnZ/9zZ2f/c2dr/3NjZ/9vZ2f/b2dn/3NnZ/93c3P/g3d3/8vHy/6ufm/86HBD/mImE//f4+f+RjIz/EgAA/ygVEf8hDwv/HwwI/xgGAf8jEAv/Oiol/2RbWf+Be3v/j4mJ/5+ZmP+ppKT/sq2t/7m1tf/Au7z/xcHB/8jFxf/Kx8f/zMjI/83Jyv/Oycv/z8rM/8/KzP/Pysz/z8rM/9DLzf/f3Nz/3tvc/97b2//e29v/3drb/93a2//e2dr/3Nna/93Y2f/c2dn/3NnZ/9zZ2f/b2dn/3Nra/97c3P/g3d3/8vLy/6ugm/88HRH/m4yH/+3t7f/Mysr/rqqr/7Ctrf+uq6z/qKSl/4B6ev8wJib/FgUC/y4dGP9lXFr/hoCA/5iSkv+moaH/sayt/7q2tv/Bvb3/x8LD/8nGxv/LyMj/zcnK/8/Ky//Pysz/0MrM/8/KzP/Qy8z/0MvN/9DLzf/f3Nz/3tzc/9/c3P/e3Nz/3tvb/93a2//e2dr/3dra/93Z2v/c2dn/3dna/9zZ2f/b2dn/3dra/97d3f/h3t7/8/Ly/6ygnP89HhL/nY2I/+rq6//e3dz/5ePi/+bj4//k4uH/5+Xl//Ly8v/S0dH/SkJC/xYFAv88Kyb/enNy/5OOjf+loaH/sq2u/7y3uP/Ev7//ycXF/8zIyP/Oycr/z8rM/8/LzP/Qy83/0MvN/9DLzf/Qy83/0czN/9HMzv/f3Nz/3tzc/97c3P/e29z/3dvb/93b2//d2tr/3dra/93a2v/d2dr/3djZ/9zZ2v/c2tr/3dvb/97d3f/h3t7/8/Lz/62gnP89HhL/m4uG//f4+f+blpb/Pywk/2JKQf9iSkD/aE9E/5+SjP/n5ub/z83N/ysgIP8kEAv/ZVpX/5OOjv+loaH/tLCx/7+7u//Hw8P/y8fH/87Kyv/Qy8z/0MvN/9DMzv/QzM3/0M3O/9HMzv/RzM7/0czO/9HMzv/e3Nz/39vc/97c3P/e3Nz/3tzc/97b2//e2tv/3dra/93a2v/d2dr/3dna/93Z2v/c2tr/3dvb/97e3f/h3t7/8/Lz/62hnf89HhL/mouF//r6+/+TjY3/JhAK/0swJv9JLiT/SC0i/0YpHP+vpaD/8vLz/21nZ/8XAwD/WUpF/5SPj/+ppKX/ura2/8TBwf/Lx8j/zsnL/9DLzP/RzM3/0c3O/9HNzv/Rzc7/0c3O/9HNzv/Rzc7/0c3O/9HMzv/f29z/39zc/97c3P/e3Nz/3tvc/97a2//e2tv/3trb/93a2v/d2tr/3dna/93Z2v/c2tr/3dvb/97e3f/h3t7/8/Lz/62hnv8+HxT/nIyG//r7+/+WkZD/KxYQ/081LP9MMij/TzUr/0YqHv+JdnD/8/T1/42Iif8bBwL/VkVA/5mUlP+yra3/wb69/8rHx//Pysz/0MvN/9HMzv/Szc7/0s7O/9HOzv/Szs//0s7P/9HOz//Rzs7/0c3O/9HMzv/g29z/3tzc/9/b3P/f29z/3tvb/97b2//e29v/3trb/97a2//d2tr/3dna/93Z2v/c2tr/39vb/9/d3f/i3t7/8vLz/66inv8/IBX/nI2H//r7/P+XkpL/LRkT/1E4L/9PNSv/Ujgu/0AjGP+PgHr/9fb3/4eCgf8jDQX/X05J/6Wiov++urr/ysfI/8/Lzf/Rzc7/0s3P/9POz//Tzs//087P/9PNz//Szc//0s7Q/9LOz//Szs//0c3P/9LNzv/g3N3/39vc/9/b3P/f3Nz/3tzc/9/b3P/e29v/3tvb/97a2//d2tv/3dna/93Z2v/c29v/3tvb/9/d3f/h3t7/8vLz/6+jnv9AIRX/m4yG//v8/f+RjIz/FgIA/zQdFv8xGxP/LhcP/1A8Nf/Mx8b/6+zt/19SUP8zGQ//dGdk/727vP/LyMj/0czO/9LOz//Tz9D/08/Q/9PQ0P/Tz9D/1M/Q/9PP0P/TztD/0s7Q/9PNz//Szc//0c7P/9HNzv/g3d7/39zd/9/b3P/f3Nz/4Nvc/9/c3P/e29z/3tvc/97b2//e2tv/3trb/97Z2v/d29v/3tvc/9/d3v/g3t7/8vLy/66inv9AIRX/nY2I//Ly8/+/u7v/hX5+/4yGhf+IgYD/j4iH/9DOzv/19vf/o5qZ/z0lG/9GLiT/pqCf/9HPz//Rzs//08/Q/9TP0P/U0NH/1NHR/9PR0f/T0dH/1NDR/9PQ0f/T0ND/08/Q/9LO0P/Szc//0s3P/9LNz//g3d7/4N3d/+Dc3f/g29z/4Nvc/9/b3P/f29z/3tvc/97b2//e2tv/3trb/97a2//d29v/3tzc/9/e3v/g3t7/8vHy/66inv9AIRX/oZKN//Ly8//s6ur/+Pj5//b29v/29vb/8/Pz/93a2v+ekI3/SzEn/zsfE/+Ie3b/19bW/9LQz//T0dH/1NLR/9TS0v/U0tL/1NLR/9TR0f/U0tL/1NHR/9TQ0f/U0NH/09DQ/9PP0P/Tzs//0s3P/9LNz//h3d3/4d3d/+Dc3f/f3Nz/39zc/9/b3P/e29z/3tzc/9/b3P/e29v/3trb/9/a2//e29v/3tzc/97d3f/f3d3/8fHy/6ygm/9HKh7/aFBH/3pkXP92YFf/dF9W/3ReVv90XlX/b1hQ/1c9NP87HRH/PiMY/4x+ev/e3t7/1dTU/9TT0//U09L/1NPS/9TT0v/U09L/1NLS/9TS0f/U0tH/1NLR/9TS0f/T0dH/09DQ/9PQ0P/Tz9D/0s7Q/9LOz//h3d7/4N3e/+Dd3f/g3N3/39vc/9/c3P/f3Nz/39vc/9/b3P/f29v/3trb/97a3P/e29z/3dzc/97d3f/e3Nz/7+/w/6yfnP9LLiP/Uzcs/0svJP9LLyT/SS4j/0gtI/9ILCL/Ry0h/1I5Lv91YVv/urKw/+rq6//b2tr/19bW/9bV1P/V1NP/1NTS/9TU0v/V09L/1dPS/9TT0v/U0tH/1NLR/9TS0f/U0dH/09HR/9LQ0P/Tz9H/08/R/9POz//h3d3/4N3e/+Hc3f/h3N3/4Nzc/9/b3P/f29z/39vc/9/b3P/f29z/3tvb/93a3P/d2tz/3tzc/97d3f/f3t7/4+Pj/97a2f/Sysn/1M7M/9XPzv/Vz83/1c/N/9XPzf/Vz83/1tDP/9/b2//v7u//7Ozs/9zc2//Z2tn/2dfX/9fW1f/V1dT/1NTT/9TU0//U09L/1dPS/9XT0v/U09L/1NLS/9TS0f/U0dH/1NHR/9PQ0f/T0ND/08/Q/9PO0P/h3d7/4N3d/+Dc3f/g3d7/4Nzd/9/b3P/f3Nz/39zc/9/b3P/e29z/3tzc/97b2//e2tz/3tzc/93c3P/e3d3/397e/+Pi4v/p6Oj/6unp/+rp6v/r6ur/7Orq/+vq6v/r6ur/6unp/+bl5f/e3d3/29ra/9vb2//a2dj/2dfW/9fW1f/V1dT/1dXU/9TU0//U1NL/1dPS/9XT0v/V09L/1NLR/9TS0v/U0dH/1NHR/9PR0f/T0ND/09DQ/9PP0P/h3d7/4d3e/+Hd3f/h3d3/4N3d/+Dc3P/f29z/39vc/9/c3P/e3Nz/3tvc/97b3P/e29z/3tvb/97b3P/d3Nz/3tzd/97c3P/d3Nz/3d3d/97d3f/d3dz/3t3c/93d3f/c3Nz/3Nzb/9zb2//c29v/2tra/9rZ2P/a19f/2dbW/9jW1f/W1dX/1dXU/9XV0//V1NP/1dPS/9XT0v/V09L/1dLS/9TS0v/V0tH/1NLR/9PR0f/T0NH/09DQ/9PP0P/i3t7/4d3e/+Hd3v/h3d7/4N3d/+Dc3f/g3Nz/39vc/97c3P/e3Nz/3tvc/97b3P/f29v/3trb/97a2//e29z/3dvc/93b3P/e29v/3dzb/93b2//c29v/29vb/9vc2//a29r/29ra/9rZ2f/a2dn/2tjY/9rX1//Z1tb/2dbW/9nV1v/X1tX/1dXU/9XV1P/V1NP/1dTT/9XT0v/U09L/1dLS/9XS0v/V0tL/1NLR/9TR0f/U0NH/09DQ/9PP0P/h39//4d7e/+Hd3v/g3d7/4N3d/+Hd3f/f3d3/39zc/97c3P/e3Nz/3tvc/9/b3P/f29z/39rb/97a2//e2tv/3drb/93a2v/d2tr/3dra/9za2v/c2tr/29nZ/9rZ2f/b2Nj/2tjY/9rX1//a19f/2tfW/9rW1v/Z1tb/2tXW/9nW1v/X1tX/1dXV/9XV1P/V1dT/1dTT/9XU0v/V09L/1dPS/9XT0v/U09L/1NLS/9TS0f/U0dH/1NDQ/9TQ0P/i3+D/4d/f/+He3v/h3d7/4d3d/+Dd3f/f3d3/39zd/9/b3P/e3Nz/3tzc/97c3P/e3Nz/39vb/97a2//e2tv/3trb/93a2v/d2dr/3dna/9zZ2f/c2Nn/29jY/9vY2P/c19f/2tfX/9rW1v/a1tb/29fW/9rW1v/a1tb/2tbW/9nW1v/Y1tb/1tXV/9XW1f/V1dT/1NTT/9TU0//U1NP/1dTS/9XT0v/V09L/1NLR/9TS0v/U0dH/1NDQ/9TP0P/i3+D/4d/f/+He3v/h3d7/4d3e/+Dd3f/g3d3/4Nzd/+Dc3P/f29z/39zc/97c3P/e3Nz/3tvc/97b2//e29v/3drb/9za2v/c2dn/3NnZ/9zZ2f/c2Nn/29nZ/9vY2P/a2Nj/2tfX/9nW1//a1tb/29fW/9nW1v/Z1tb/2dbW/9nW1v/Z1tb/19XV/9bW1f/V1dT/1NXU/9TU0//V1NP/1NTT/9XT0v/W09L/1dLS/9XS0v/U0tH/1NHR/9TQ0f/i4OD/4d/f/+He3//h3t//4d3e/+Hd3v/h3d7/4d3d/9/d3f/f3Nz/39zc/97c3P/f29z/3tzc/97c3P/e29v/3trb/93Z2v/c2dr/3Nra/9zZ2f/d2Nn/3NnZ/9vZ2f/a2dn/2tfX/9rX1//a19b/2tbW/9rW1v/a1tb/2dbW/9nW1v/Z1tb/2NbV/9fW1f/W1tT/1dXU/9bU1P/V1dP/1dTT/9XT0//V09P/1dPS/9XT0v/U0tH/1NHR/9TR0f/i4OD/4t/g/+Hf3//h39//4d7f/+Hd3v/h3d7/4N3e/+Dd3f/g3N3/39vc/9/b3P/f3Nz/3tzc/97c3P/e29v/39rb/97a2//e2dr/3dra/93Z2v/c2dn/29nZ/9vZ2f/b2Nj/2tjY/9rX1//a19b/2tbW/9rW1v/a1db/2dbW/9jW1v/Z1tb/2dbW/9jW1v/X1tX/1tXU/9bV1P/W1dT/1dXT/9XU0//V1NP/1dPS/9XT0v/V0tL/1NLR/9TS0f/j3+D/4t/g/+Lf3//h39//4d/f/+He3v/h3d7/4N7e/+Dd3v/g3N3/4Nzd/9/c3P/e3Nz/39vc/97c3P/e29v/3tvb/97a2//e2tr/3dna/93Z2v/c2dn/3NnZ/9vZ2f/b2dn/2tjY/9rY2P/a19f/2tfW/9vW1v/a1tb/2dbW/9rX1v/Z1tb/2NbW/9jW1v/Y1tb/19bV/9fV1f/W1dX/1dXU/9XV0//V1NP/1dTT/9XT0//V09L/1dLS/9XS0f/j4OD/49/g/+Lf3//i39//4d/f/+He3//h3t7/4d3e/+Dd3v/g3d7/4N3d/+Dc3P/e3Nz/39vc/9/b3P/e29z/3tvc/97b2//e2tv/3dna/93Z2v/c2dr/3NjZ/9vZ2f/b2dn/29nZ/9rY2P/a2Nj/2tfX/9vX1v/a19b/2tbW/9rW1v/a1tb/2dbW/9rW1v/Z1tb/2NbV/9fW1f/X1dX/1tXU/9XV1P/W1NP/1dTT/9XT0v/V09P/1dLS/9XS0v/j4OD/49/g/+Pf4P/i4OD/4t/f/+He3//h3t7/4d3e/+Hd3v/g3d3/4N3d/+Dc3f/f3Nz/39zc/9/c3P/e3Nz/3tvc/97c3P/d29v/3drb/93a2v/d2tr/3dnZ/9zZ2f/c2dn/29nZ/9rZ2f/b2Nj/29fX/9vX1//a19b/2tfW/9nW1v/a1tb/2tbW/9rW1v/Z1tb/2NbW/9fW1f/X1tX/1tbV/9bW1f/W1dT/1tTT/9bU0//V1NP/1dPT/9bS0v/j4OH/4uDg/+Pf4P/i3+D/4t/f/+Le3//h39//4d/f/+He3v/h3d3/4N3d/+Dd3f/g3N3/39zc/9/b3P/f3Nz/3tzc/97c3P/e3Nz/3dvb/97a2//d2tr/3Nna/9zZ2v/c2dn/29jZ/9rZ2f/a2dn/3NjY/9vY1//a19f/2tfW/9rW1v/a1tb/2tbW/9nW1v/a1tb/2dbW/9jW1f/X1tb/1tbV/9bW1P/W1dT/1tXU/9bU0//W1NP/1tPS/9fT0v/j4OH/4+Dh/+Pg4P/i4OD/4t/g/+Pf3//i39//4d/f/+He3v/g3d7/4N3d/+Dd3f/g3N3/39zc/9/c3P/e3Nz/3tzc/9/c3P/f3Nz/3tvc/97a2//d2tr/3dra/9za2v/c2dn/3NnZ/9vY2f/b2Nn/29jZ/9vY2P/a2Nf/29fW/9rW1v/a1tb/2tfW/9vX1v/b19b/2tbW/9nX1v/Y1tb/19bV/9bW1f/W1tT/1tXU/9fV1P/W1NP/1tTT/9bT0//k4OH/5ODh/+Ph4f/j4OD/49/g/+Pf4P/i4OD/4eDg/+Hf3//g3t7/4N3e/+Hd3v/g3d3/4Nzd/+Dc3f/f3Nz/3tzc/97c3P/e3Nz/3tzc/97b2//e2tv/3dra/9za2v/c2tr/3NnZ/9vZ2f/c2dn/29nZ/9vZ2P/a2Nj/2tfX/9rX1//b19b/29fW/9vX1v/b19b/2tfW/9rX1v/Z19b/2NfW/9fW1f/X1tX/19bV/9fW1P/W1dT/1tXT/9bU0/8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
        """
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray.fromBase64(icon_base64.encode("utf-8")))
        return QIcon(pixmap)