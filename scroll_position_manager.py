# scroll_position_manager.py
class ScrollPositionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScrollPositionManager, cls).__new__(cls)
            cls._instance.scroll_positions = {}
        return cls._instance

    def save_scroll_position(self, path, position):
        if path:
            self.scroll_positions[path] = position

    def get_scroll_position(self, path):
        return self.scroll_positions.get(path, 0)
